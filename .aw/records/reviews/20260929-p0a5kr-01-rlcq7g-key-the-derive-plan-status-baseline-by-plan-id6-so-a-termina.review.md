# Review findings: plan rlcq7g

- Subject-Id: rlcq7g
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f5c6114b` in a lane worktree. No pre-review snapshot was needed: the plan was
committed and unmodified (`git status --short` on the plan path returned nothing). Structural preflight
`aw ipd lint --phase author --agent` reported `clean` / exit 0 with no advisories, and
`--phase review-finalize` still conforms after every revision below.

THE PLAN'S PREMISE IS CORRECT AND I RE-MEASURED IT RATHER THAN TRUSTING IT. The plan's own figures were
taken at `afb948ce`, which is 291 commits behind current HEAD, so every load-bearing number was
re-derived:

```text
baseline keys: 777        baseline key slash-depths: {4: 777}
live terminal: 882        intersection: 732        pending-keyed baseline entries: 45
live depths: {4: 882}
declared_id6 none: 0 of 882    dupes: []    slot/declared disagreements: 0
```

The re-key itself was prototyped end to end and is lossless:

```text
rekeyed entries: 732   collisions: 0
values multiset equal: True
mismatches after rekey: 0        coverage: 732 / 732
```

F-5's resurrection trap is real and I confirmed it in the direction that matters: all 45 pending-era
ids (not the 38 the plan states) are now live in a terminal directory, and for all 45 the derived
status has legitimately changed since capture (`u8tabj`, `ex539u`, `ozcfjr`, `63h054` all
`'approved' -> 'executed'`). None of the 45 overlaps the 732 keys E-01 carries, so the specified
transform is safe; a transform over all 777 would ship 45 false mismatches.

F-7's green-to-green claim holds: `python3 -m pytest tests/test_history_order.py -o addopts=""` reports
`6 passed in 0.31s` today, and a bare full suite reports `3246 passed, 2 skipped, 3 warnings in 57.42s`.

SIX FINDINGS WERE ADDED AT REVIEW AND ALL WERE FIXED IN PLACE. Two of them (F-11, F-13) would each have
silently defeated part of the plan's own purpose while every check it listed still passed, which is the
same failure shape the plan exists to end.

F-11 is the serious one and it is self-contradicting rather than merely arguable. OQ-01 resolved the
floor to a pure fraction while stating the requirement a pure fraction cannot meet: that "an id6-keyed
intersection that silently fell to a handful of entries would make the guard vacuous while still
passing". The fraction's denominator IS the fixture, so shrinking the fixture shrinks the bar:

```text
len(baseline)= 732  95% threshold=  695.40  a fixture of 732 entries all found PASSES
len(baseline)= 100  95% threshold=   95.00  a fixture of 100 entries all found PASSES
len(baseline)=  10  95% threshold=    9.50  a fixture of 10 entries all found PASSES
len(baseline)=   1  95% threshold=    0.95  a fixture of 1 entries all found PASSES
```

F-13 is the one an executor was most likely to hit. 33 of the 732 values are JSON `null`, not strings
(plan `63h054` E-01 specified "`null` for None" because `derive_plan_status` returns `Optional[str]`).
E-01 said only "carry the EXISTING frozen value across unchanged", so the natural `if value:` transform
drops 33 entries and converts 33 real comparisons into none, leaving 699 id-shaped keys with an equal
value multiset: every literal condition E-01 stated except the count. The measured value distribution
of the compared 732 is `{'executed': 470, 'draft': 133, 'to-review': 66, 'None': 33, 'approved': 22,
'reviewed': 8}`. Independently, a naive `sorted(values)` in V-01's own evidence command crashes:

```text
TypeError: '<' not supported between instances of 'NoneType' and 'str'
```

F-16 strengthens the plan against itself. F-3 described the archive annihilation as simulated and
noted no plan is sharded yet, but `aw archive plans` has a bare-sweep mode defaulting to 14 days
(`plans_archive.DEFAULT_SWEEP_AGE_DAYS = 14`) and `plans_archive.sweep_candidates` returns 614 plans
today, all inside the compared intersection:

```text
intersection: 732
of those, in default 14d sweep: 614
intersection remaining after ONE bare `aw archive plans --apply`: 118
```

So the breaking operation is one argument-free command against a floor of 700, not a deliberate
full-tree sharding. That bears on the plan's `- Priority: low`, which I left alone because priority is
the maintainer's call, but it is now recorded where an approver will see it.

F-12 and F-17 are corrections that make the plan honest rather than changing its direction. The
95-percent floor is slightly LESS sensitive than the absolute it replaces to the one remaining real
cause (fires at 37 missing ids, where 700 fired at 33), and F-6's "102 legacy names carry no id6
identity slot" misattributes its own arithmetic: only 4 of the 102 fail to parse as clustered names,
while 98 parse fine and are rejected by `selectors.filename_slot_id6`'s deliberate all-letters guard
`_HAS_DIGIT_RE` (mirroring `check_engine._is_real_id6` so a slug word like `assess` is not mistaken for
an id6). Restricted to the 732 keys E-01 carries the figure is 95, not 102. The conclusion is unchanged
and stronger: the filename resolver is wrong BY DESIGN for most canonical names too.

I also corrected two V-items that would have accepted evidence proving nothing. V-03 asked for "a few
extra ids" as its coverage negative; measured against the 732-entry fixture, 3, 10 and even 38 phantom
ids all leave the assertion PASSING, and 39 is the smallest count that fires, so a "few" would have
produced a green run offered as a negative. V-02's perturbation instruction did not say which edits
actually move the derived status; the `AGENTS.md`-sanctioned dated cross-reference note does NOT
(measured over all 262 non-`executed`-valued and `null`-valued compared entries: zero flips), whereas a
later-dated `draft` record flips to `draft` and deleting the `executed` record flips to `approved`.

The gate was missing two required elements and both were added: a SCOPE FENCE (declared as a
reconciliation declaration, with an explicit "made and then JUSTIFIED" clause and no stop directive, per
the 2026-09-01 maintainer ruling) and the CONDITIONAL lifecycle ownership (runner-owned in a managed
lane per `AW-LIFECYCLE-ROLE-001`, executor-owned only in an unmanaged run). A "what a human would be
approving" paragraph was added, naming what the review itself changed.

RIGHT-SIZING: four E-items over two files, each one concern, each independently verifiable. No split is
warranted and the linter raised no `IPD-Z602`. P16 (test outcomes, not code structure) is satisfied and
is explicitly the warrant for this fixture class, since the derived status of frozen plan text IS the
artifact under test; the scope fence now also forbids adding any `inspect`/`ast`/regex source-reading
assertion.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D. Anti-regression; G. Plan executability | `.aw/records/plans/pending/20260929-p0a5kr-01-rlcq7g-...ipd.md` E-03 and OQ-01 (quoted string "at least 95 percent of the fixture's entries") | A pure fraction-of-baseline floor is VACUOUS against a shrinking fixture, and OQ-01 chose it while stating the requirement it cannot meet ("an id6-keyed intersection that silently fell to a handful of entries would make the guard vacuous while still passing"). Measured: a 10-entry fixture with all 10 found scores 100 percent and passes; so does 1 of 1. The denominator is the artifact being bounded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now carries TWO assertions: the coverage fraction PLUS a retained `len(baseline) >= 700` non-vacuity floor on the fixture's own size, with a comment stating why an absolute is legitimate for a frozen authored artifact though it rotted when bounding the live intersection. OQ-01 rewritten to "BOTH" with the measurement. V-03 now requires a truncated-fixture negative that a fraction-only implementation passes. |
| PR-002 | MEDIUM | IN-SCOPE | D. Anti-regression | Plan E-03 Expected outcome (quoted string "arithmetically unreachable by any number of renames or archive shards") | The 95-percent floor is LESS sensitive than the absolute it replaces to the one genuine remaining cause. Measured at 732 entries: it first fires when more than 36 baseline ids go missing, where the old 700 fired at 33. The plan claimed only the improvement and not the regression. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12 recording the measured sensitivity in both directions, cited from OQ-01 and from proposed change 3, so the 95 figure is a known cited choice rather than an unexamined default. Goal now carries an explicit "what this does not claim" paragraph stating the guard is not made more sensitive. |
| PR-003 | HIGH | IN-SCOPE | A. Correctness and data integrity; E. Testing | Plan E-01 (quoted string "carry the EXISTING frozen value across unchanged"); `tests/fixtures/derive_plan_status_baseline.json`; plan `63h054` E-01 (quoted string "`null` for None") | 33 of the 732 values to be carried are JSON `null`, not status strings, and neither E-01 nor its Expected outcome named them. A natural falsy-filtering transform silently drops 33 entries and converts 33 real comparisons into none, while still satisfying every literal condition E-01 listed except the count. V-01's own evidence command also crashes on a bare `sorted()` over those nulls. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now has a dedicated "PRESERVE JSON `null` AS A FIRST-CLASS VALUE" paragraph with the count and the reason, its Expected outcome names all 33, V-01 requires printing the null count and using a `None`-safe sort key, and a Step 0 convention bullet records the fixture's `Optional[str]` value domain. |
| PR-004 | MEDIUM | UNDER-SCOPE | A. Correctness; D. Anti-regression | Plan E-02; `agent_workflows/selectors.py` symbol `read_front_matter_id` (returns `Optional[str]`); `agent_workflows/check_engine.py` rule `check.id6-collision` | Keying by id6 opens a silent-coverage-loss mode that path-keying was structurally immune to: a path is unique by construction, an id6 only by convention. A duplicate declared `- Id:` makes a dict build keep the last visited and drop the other; a plan with no `- Id:` yields `None` and collapses all such plans onto one key. Clean today (882/882, 0 collisions) but unguarded, and silent coverage loss is the exact defect class this plan exists to end. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now collects duplicate ids and `None`-id files while building the map and asserts both empty, naming offending paths, explicitly without depending on `check.id6-collision` having been run. Expected outcome updated; V-02 requires the distinct-id-count evidence plus a demonstration that the new assertion fails on a two-plans-one-id temp tree. Added F-14. |
| PR-005 | MEDIUM | IN-SCOPE | E. Testing; G. Plan executability | Plan E-04 (quoted string "Extract whatever logic both this test and `test_whole_tree_derivation_is_unchanged` need into a module-level helper") | E-04's shared-helper mandate defeats its own purpose as written: the whole-tree guard resolves its root from `_repo_root()` while the new test needs a temporary root, so a helper that hard-codes the root or asserts internally cannot serve both and the "cannot drift apart" guarantee is false. E-04 also did not require the discriminating negative to come from a plan-history edit, and a baseline-value edit would prove only that two unequal strings compare unequal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now mandates a root-parameterized, assertion-free helper returning data with every `assert` left in the two test methods, mandates a history-edit negative, names two perturbations measured to flip the derived status, points the executor at the existing `_fixture_plan_text` helper rather than a second builder, and notes the sanctioned dated note measurably does NOT flip. V-04 requires the helper signature and both call sites. |
| PR-006 | MEDIUM | IN-SCOPE | C. Architecture and operability | Plan F-3 (quoted string "No live terminal plan is sharded yet"); `agent_workflows/plans_archive.py` symbols `DEFAULT_SWEEP_AGE_DAYS` (= 14) and `sweep_candidates` | F-3 understates its own case in the plan's disfavor, describing the archive annihilation as simulated. Measured: the bare sweep mode defaults to 14 days and `sweep_candidates` returns 614 plans today, all 614 inside the 732-key compared intersection, so ONE argument-free `aw archive plans --apply` leaves the intersection at 118 against a floor of 700. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 amended with the measured sweep figures and the 732 -> 118 result; added F-16 recording that this bears on the plan's `- Priority: low` (priority itself left to the maintainer). Goal's new paragraph cites it as the class of failure actually being removed. |
| PR-007 | LOW | IN-SCOPE | Evidence accuracy | Plan F-6 (quoted string "fails on 102 of the 777 baseline keys, whose legacy names carry no id6 identity slot"); `agent_workflows/selectors.py` symbols `filename_slot_id6` and `_HAS_DIGIT_RE` | F-6's total is right but its arithmetic is misattributed, misdirecting a reader about WHY the resolver fails. Only 4 of the 102 fail to parse as clustered names; 98 parse fine (both of F-6's own examples yield a slot token) and are rejected by the deliberate all-letters guard `_HAS_DIGIT_RE`. Against the 732 keys E-01 carries the count is 95, not 102. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 rewritten with the 95/732 figure, the 4-versus-98 split, and the real mechanism (mirroring `check_engine._is_real_id6` so a slug word like `assess` is not read as an id6). E-01 now explicitly forbids `filename_slot_id6` and names the 95. Added F-17. Conclusion unchanged and strengthened. |
| PR-008 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | Plan `## Approval and execution gate` as authored (contained the commit rule and the finalize lint, but no scope fence and no ownership conditional) | The gate lacked two required execution-contract elements: a SCOPE FENCE declaring the intended surface for post-hoc reconciliation, and the CONDITIONAL lifecycle ownership. It also instructed the plan be "transitioned ... through the tooled lifecycle" without naming who owns the transition, which in a managed lane is the runner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a scope fence written as a declaration with a "made and then JUSTIFIED" clause and no stop directive (2026-09-01 ruling), enumerating eight negative constraints including not editing `derive_plan_status`, not generating fixture values by re-deriving, not making the fixture rename-rewritable, not relaxing the terminal-bucket restriction, and no source-reading assertions (P16). Added the runner/executor conditional citing `AW-LIFECYCLE-ROLE-001` and the never-hand-roll rule. Added a "what a human would be approving" paragraph. |
| PR-009 | LOW | IN-SCOPE | E. Testing (validation bar) | Plan `## Required tests / validation` (quoted string "A full bare `python3 -m pytest` must pass") | The full-suite bar named no measured baseline, so an executor facing a failure could not tell a regression from pre-existing breakage, and the repository has a live precedent of plans that must declare an expected pre-existing failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Pasted the review-measured baseline (`3246 passed, 2 skipped, 3 warnings in 57.42s`, 207 deselected as `slow`/`livecorpus`) into the validation section and into V-04, stating the bar is zero failures and not a failing-set delta. Also re-verified and recorded the sole-consumer grep in the Scope check. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01 resolved the floor to a fraction alone, but its own rationale demands protection a fraction cannot give. Accept the resolution, reopen it as a blocking question, or fix it? | FIX IT IN PLACE as BOTH floors, and rewrite OQ-01 to say so with the measurement. | (a) Accept the fraction alone: rejected on arithmetic, it is vacuous against a shrinking fixture and OQ-01's own words forbid that outcome. (b) Reopen as `- Blocking: yes`: rejected, the repository already answers it. OQ-01 states the non-vacuity requirement, and `63h054` E-01 establishes the fixture is a machine capture whose size is an authored fact, so keeping an absolute on the FIXTURE is derivable from the plan's own record rather than a maintainer preference. (c) Drop the floor entirely: rejected, that is the vacuity OQ-01 names. (d) Make the fraction relative to the LIVE terminal population instead: rejected, that reintroduces coupling to a drifting live count, which is the rot this plan removes. | Measured: `found >= 0.95 * len(baseline)` passes at 10 entries of 10 and at 1 of 1. OQ-01's own quoted requirement. `63h054` E-01's "machine capture" framing. The old 700 bounded the live-tree intersection, which every move shrank; the new one bounds the fixture, which only an edit changes. | yes |
| D-2 | F-13's null-dropping hazard: is naming it in E-01 enough, or does the plan need a spike/probe E-item to prove the transform preserves nulls? | NAME IT in E-01 with the count and mechanism, and demand the count in V-01's evidence. No new E-item. | (a) A spike E-item to prototype the transform: rejected as unnecessary, the transform was already prototyped end to end at review (732 -> 732, value multiset equal, 0 mismatches), so the demonstration exists and belongs in the findings rather than as unperformed work. (b) Leave E-01 as-is since "carry unchanged" arguably covers nulls: rejected, the natural falsy-filter is the likely implementation and every check E-01 listed except the count would still pass, which is precisely a silent-coverage-loss defect. (c) Change the fixture's `null` convention to a sentinel string: rejected outright, it would edit 33 frozen values and break the `63h054` capture contract. | Measured 33 nulls in the compared 732; `derive_plan_status` returns `Optional[str]`; plan `63h054` E-01 quoted string "`null` for None"; the `TypeError` from a bare `sorted()` over the value list. | yes |
| D-3 | F-3/F-16 shows one default `aw archive plans --apply` takes the intersection from 732 to 118. Should the review raise the plan's `- Priority: low`? | NO. Record the measurement in F-3 and F-16 where an approver sees it; leave `- Priority:` untouched. | (a) Raise it to high or medium: rejected, priority is a maintainer judgement about what to do next (explicitly a human's call under the repository's own guidance on scope, priority and risk appetite), and the plan already carries `- Blocks-Release: next`, which is the gate that actually governs shipping. (b) Say nothing and leave F-3 as authored: rejected, the plan understated its own urgency and an approver weighing `low` deserves the real number. (c) Raise it as a blocking open question: rejected, nothing is blocked; the fix direction is unchanged either way. | `plans_archive.DEFAULT_SWEEP_AGE_DAYS = 14`; `sweep_candidates` returns 614; 614 of the 732 compared keys are candidates; intersection after sweep = 118 against floor 700. The item already carries `- Blocks-Release: next`. | yes |
| D-4 | F-5 says 38 pending-era ids are now terminal with changed status; I measured 45. Correct the number, or leave it? | Correct the OPERATIONAL instruction rather than relitigating the figure: V-01 now demands proof the pending-era id set is DISJOINT from the rewritten fixture's keys (measured empty), which is strictly stronger and needs no count. | (a) Edit F-5's 38 to 45 and stop there: rejected as insufficient, the count is incidental and the real requirement is disjointness; a corrected count still leaves V-01 asking for a weaker per-value check. (b) Leave 38 unchallenged: rejected, V-01 referenced "the 38 pending-era resurrection ids" as its evidence target, so a wrong count was load-bearing for a validation item. (c) Treat the discrepancy as an error in the plan's favor: rejected, it is against the plan (45 traps, not 38), so the hazard is slightly larger than stated. | Measured: all 45 pending-era ids resolve to a live terminal plan and all 45 have a changed derived status; the difference from 38 is that 7 of the 45 have non-canonical filename slots, so a `filename_slot_id6`-based count misses them while the declared-id reading does not. Intersection of the 45 with the rewritten 732 keys is EMPTY. | yes |
| D-5 | V-03's coverage negative said "a few extra ids", which measurably does not fire. Fix the V-item, or lower the threshold so a few ids do fire? | FIX THE V-ITEM: require at least 39 phantom ids and state why 3, 10 and 38 are insufficient. | (a) Lower the 95 percent so a handful fires: rejected, tightening the coverage floor would make routine terminal-tree churn (a deleted plan, a plan pulled back out of `executed/`) redden the suite, trading this bug for a noisier version of it. (b) Leave "a few" and trust the executor: rejected, the plan's whole complaint is about evidence that looks like proof and is not; a green run pasted as a negative is exactly that. (c) Drop the coverage negative: rejected, without it the assertion is never shown to fire at all. | Measured against the 732-entry fixture: 3, 10 and 38 phantom ids all leave the assertion passing (`732 >= 0.95 * 770`); 39 is the smallest count that fires. | yes |

### Deferred and open

- (none). All nine findings were FIXED in place. No finding reached the repository's gate threshold
  (`review_findings_gate.block_at`, default `HIGH`) while unfixed, so no escalation to a
  `- Blocking: yes` open question was required. Both pre-existing open questions (OQ-01, OQ-02) remain
  `- Blocking: no` and `- Status: resolved`; OQ-01's resolution was rewritten under PR-001 and D-1.
- No `Reversible: no` decision was taken. Every decision above edits a plan or a test-only artifact and
  can be undone by a later editor; nothing published, migrated, deleted, or released is involved.
