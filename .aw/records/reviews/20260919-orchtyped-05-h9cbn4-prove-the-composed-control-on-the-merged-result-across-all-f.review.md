# Review findings: plan h9cbn4

- Subject-Id: h9cbn4
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `c58ec3ab`. The plan on disk was byte-identical to the sealed lane input (`diff`
reported no difference) and `git status --short` was empty before any edit, so no pre-review snapshot was
needed. Structural preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0,
both before and after the revisions; the watermark is unchanged at 05, because every finding was fixed by
correcting or narrowing an existing instruction rather than by adding an E-item.

DISCLOSURE: the same agent/model authored this plan, so this is a SELF-REVIEW, and its value rests on
EXECUTING claims rather than re-reading them. This round resolved all seven probe functions and summed
their AST spans, ran the probe suites and the BARE suite, computed `aw check all` twice, diffed the
probe's test file against the Set's own authoring commit, exercised the probe payload on both
continuation-line shapes, and read `evaluate_set_retirement`, `ipd_lint.check_checkpoint` and
`ipd_schema._VALIDATION_RULES` in source.

WHAT SURVIVED, and most of this plan did. Its central premise is exactly right and I confirmed the
mechanism rather than trusting it: `runner_shared.evaluate_set_retirement` contains ZERO references to
`E-`, `V-`, `items`, `checklist`, `execution state`, `lint` or `checkpoint` (all seven checked
individually), so a whole-Set verification parked on the parent genuinely would be marked complete
unperformed, and this child is the correct R1b remedy. The `svacmz` precedent is real
(`- Item-Dependencies: executed:skn8uk, executed:ty7w6o, executed:dy9ymn`). Criterion 4's
"this Set is its own proof" claim holds: `d1u4sy`'s five rows read exactly `E-01 CONFIRM dpdyed REACHED
executed` through `E-05 CONFIRM h9cbn4 REACHED executed`. PR-005's probe-payload measurement reproduces
precisely (a bare indented continuation line IS in the payload and the excerpt; the same words as
`- Context:` are NOT). All three real parent-only item texts are quotable verbatim at HEAD. And the
spec's 476-line figure for the seven probe functions is still EXACT when re-derived by AST.

WHERE THIS REVIEW SPENT ITS EFFORT: one BLOCKER that would have failed this child for somebody else's
legitimate work, and two HIGHs where the plan asserted less or more than it could.

**1. The byte-unchanged pin already fails at HEAD, and its likely remedy is a shared-checkout violation
(PR-501, BLOCKER).** E-03 and V-03 require `tests/test_orchestrator_probe.py` byte-unchanged "across the
WHOLE Set's diff (a diff against the Set's base commit)". Measured: the maintainer's commit `75b90271`
("test: tabulate eleven more suites") rewrote that file on 2026-09-19 at 16:26, which is AFTER this Set
was authored at 14:22 (`a4808752`), and `git diff --stat a4808752 HEAD -- tests/test_orchestrator_probe.py`
reports 2270 insertions and 529 deletions, taking it from 1265 lines to 3006. So the pin is unsatisfiable
before a single child has run, through no fault of this Set. That matters more than a wrong assertion
usually would, because of WHICH two exits it leaves: report a false failure on the Set's own completion
gate, or REVERT a co-worker's refactor so this child's validation passes. The second is the likelier
choice under pressure to finish a Set, it is forbidden outright by the shared-checkout rule, and it would
be committed by the one child whose entire purpose is honest verification. Note the spec does not demand
bytes: criterion 9 asks for the probe's test file passing UNEDITED, and the honest reading is unedited BY
THIS SET. The pin is now three-part and each part is harder to fake than a byte compare: absence from the
SET'S OWN diff (the union of the five children's commits, not a range over main, which silently includes
every other party's work and is the defect being fixed); the seven functions resolving with their AST span
re-derived (476, measured); and the suite passing (96 passed across the probe and cache suites, with
`TheExcerptHasAKnownLIMIT` surviving the refactor at line 1228).

**2. Criteria 10 and 11 are already a sibling's work, and what this child uniquely adds was unstated
(PR-503, HIGH).** Child 03's E-04 covers criteria 9 AND 10 (its expected outcome reads "the two rule ids
differ") and its E-05 covers criterion 11 with the non-vacuous injected-counter method. This plan's own
deferral section says criteria 2, 5, 6, 7, 8 and 12 are CITED rather than re-run because re-running
duplicates a sibling's assertion, yet E-04 silently re-ran 10 and 11. The boundary was applied
inconsistently rather than wrongly drawn. What child 03 genuinely cannot observe is that in its worktree
child 04's migration has not happened, so every live orchestrator is non-conforming; on the MERGED tree
the case inverts, and a queue of CONFORMING orchestrators must pass the shape check and REACH the probe.
That is the ordering's other half and it is the real contribution. E-04 now requires a MIXED queue and
fails on single-non-conformer evidence.

**3. The criterion-1 grep reads a shipped design as a violation (PR-502, HIGH).** E-01 requires proving
"no second child-table scan" exists. Two legitimate readers of the `## Child IPDs` heading already exist
and predate this Set: `ipd_set_plan.parse_child_table` (`:344`, returning the order graph) and
`runner_shared.child_table_rows` (`:7008`, returning full cell tuples and deliberately shared by the
probe cache and `parse_declared_child_orders`). Child 01's E-02 is required to COMPOSE them. A grep for
"one scanner" therefore reports two known-good hits, and the same holds for `RECOGNIZED_STATUS`, which
legitimately appears at its definition (`ipd_schema:262`), in its own validator (`:355`) and in
`completion.py:537`. The claim to prove is that THE CONFORMANCE RULE has one definition and neither
consumer re-derives it, so the search must enumerate expected hits in advance and account for every
actual hit. Left as written it produces either a false violation or a victory declared without looking.

**4. The three real fixtures will be gone by the time this runs (PR-505, MEDIUM).** E-02's note said the
items "may have been MIGRATED by child 04". They WILL have been: child 04 rewrites exactly these plans.
A fixture reading the live files post-migration would assert that a CONFORMING row is refused, which
inverts criterion 3; and a test that reads a live plan file is a test of child 04's migration rather than
of the grammar, breaking whenever anyone edits those plans. Now literal in-file fixtures with the git
revision cited.

**5. The `aw check all` baseline is stale within the hour (PR-504, MEDIUM).** The plan correctly requires
a per-rule delta rather than absolute green, but I measured the total move from 243 findings at
`c138a219` to 270 at `c58ec3ab`, about twenty minutes apart, entirely from other parties' merges and with
no contribution from this Set. So the baseline must be taken in the executing worktree at start and never
quoted from a document. I recorded the rule distribution as orientation only (`check.scope-drift` 169,
`check.ipd-uncarried-obligation` 88, the rest single digits), and named those two rules specifically
because child 04's twelve rewritten plans could legitimately move them, making a move there a fact to
explain rather than automatically a regression.

**6. One more measurement worth recording (F-10, LOW).** The suite pass total moved 7305 -> 7080 across
this Set's own lifetime, purely from `75b90271`'s test tabulation with no behavior change. That is
independent evidence for the plan's existing "compare failing node ids, not totals" rule, and recording
it stops an executor reading the drop as breakage. The baseline's one real failure is
`test_no_pending_plan_is_refused_on_a_verdict_today`, naming three `reaskscore` plans another party is
editing; I confirmed it pre-existing by running the node alone.

WHAT I DELIBERATELY DID NOT CHANGE. The five-item shape, the dependency chain and the no-product-code
boundary are all correct and I left them alone; I strengthened the boundary instead, by naming
`tests/test_orchestrator_probe.py` as a path that never becomes declarable here and by adding an explicit
deferral forbidding a revert of another party's work. I did not weaken any criterion: the byte pin was
replaced by three checks that cannot be satisfied by reverting a co-worker, and E-04 is materially harder
than as authored. OQ-01 stays `open` and non-blocking, and I verified every mechanical claim in its
rationale from source rather than leaving it as reasoning; I also recorded its one honest gap, that the
prohibition on weakening a criterion is a rule and not a mechanism, which is the same self-assessment
limit spec Section 3a limit 3 already states.

VALIDATION RUN AT REVIEW. `aw ipd lint --phase author --agent` and `--phase review-finalize --agent` both
report `clean`, 0 findings, exit 0. Bare suite at HEAD: `1 failed, 7080 passed, 3 skipped, 2 xfailed`
(89.03s), the single failure being the pre-existing `reaskscore` corpus case, confirmed by running the
node alone. Probe suites: `python3 -m pytest tests/test_orchestrator_probe.py
tests/test_orchestrator_probe_cache.py -o addopts=""` -> `96 passed`. `aw check all` reports 270 findings
with ZERO against this plan. Every mechanical claim above was produced by running code, not reading it:
the seven `hasattr` checks and the AST span sum (476); `probe_cache_payload`/`orchestrator_probe_excerpt`
on both continuation-line shapes; the seven-token absence scan over `evaluate_set_retirement`'s source;
`ipd_schema.VALIDATION_RESULTS` and `_VALIDATION_RULES`; `check_checkpoint`'s `pre-transition` branch; and
the git archaeology on `75b90271` versus `a4808752`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | BLOCKER | IN-SCOPE | A (correctness); D (invariants); shared-checkout rule | `git diff --stat a4808752 HEAD -- tests/test_orchestrator_probe.py` (2270 insertions, 529 deletions, 1265 -> 3006 lines); `git log -1 --format='%ci' 75b90271` = 16:26 vs `a4808752` = 14:22; `TheExcerptHasAKnownLIMIT` at `tests/test_orchestrator_probe.py:1228`; seven functions resolving at a 476-line AST span | The byte-unchanged pin on the probe's test file ALREADY FAILS at HEAD, before any child runs, because the maintainer rewrote that file two hours after the Set was authored. The item is unsatisfiable through no fault of this Set, and its two exits are a false failure on the Set's completion gate or a REVERT of a co-worker's refactor to make this child's own validation pass, which the shared-checkout rule forbids and which is the likelier choice under pressure. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-03/V-03 replaced the byte compare with three pins that survive a third party's refactor: absence from the SET'S OWN diff (union of the five children's commits, not a range over main), the seven functions with their AST span re-derived, and the suite passing with `TheExcerptHasAKnownLIMIT` named. A deferral forbidding any revert was added, the Scope check names the file as never-declarable here, and F-7 records the measurement. |
| PR-503 | HIGH | OVER-SCOPE | C (architecture); E (verification) | `0xmk4e` E-04's expected outcome ("the two rule ids differ") and E-05's injected-counter method, both read at review; this plan's own deferral list for criteria 2, 5, 6, 7, 8, 12 | Criteria 10 and 11 are already asserted by child 03, so E-04 re-ran a sibling's validated work while this plan's own deferral section forbids exactly that for six other criteria. The genuine addition (a post-migration CONFORMING queue passing the shape check and REACHING the probe, which child 03's pre-migration worktree cannot contain) was unstated. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now requires a MIXED queue proving both halves and a statement of what it adds over child 03; V-04 requires the conforming half with a nonzero probe count and FAILS on single-non-conformer evidence; the deferral section now states the boundary binds 10 and 11 too; F-8 added. |
| PR-502 | HIGH | IN-SCOPE | A (correctness); G (executability) | `ipd_set_plan.py:344`; `runner_shared.py:7008` and `parse_declared_child_orders`'s docstring; `ipd_schema.py:262`/`:355`; `completion.py:537` | The criterion-1 grep for "no second child-table scan" fires on TWO legitimate pre-existing scanners that child 01 composes rather than replaces, and the "second status list" search has three known-good hits. As written it yields either a false violation against shipped design or a victory declared without accounting for the hits. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 requires enumerating expected hits BEFORE searching and accounting for every actual hit as the one rule, a named pre-existing scanner, or a violation; V-01 fails both a false conclusion and an unaccounted hit; F-5 refined; a Step-0 convention added. |
| PR-505 | MEDIUM | IN-SCOPE | A (correctness); E (verification) | all three item texts quoted verbatim from HEAD at review; child 04's Scope declaring `.aw/records/plans/pending` | E-02 said the three real items "may have been MIGRATED by child 04". They WILL have been. A fixture reading the live files post-migration asserts that a CONFORMING row is refused, inverting criterion 3; and a live-file test becomes a test of the migration rather than of the grammar. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 requires the three texts embedded as LITERAL fixtures with their git revision cited and forbids reading the live plan files; V-02 fails evidence taken from the post-migration tree; F-9 added. |
| PR-504 | MEDIUM | IN-SCOPE | E (testing); honest baselines | `aw check all` = 243 findings at `c138a219`, 270 at `c58ec3ab`, twenty minutes apart from unrelated merges; per-rule distribution captured | The plan rightly required a per-rule delta but did not say the baseline must be taken in the executing worktree. The total moves fast enough that any plan-recorded figure is stale within the hour, which invites comparing against a dead number. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-05 and V-05 require the baseline taken in the executing worktree at start and never quoted, with the measured 243 -> 270 move as the reason; `check.scope-drift` and `check.ipd-uncarried-obligation` named as the two rules child 04's twelve rewritten plans could legitimately move; F-6 quantified; a Step-0 convention added. |
| PR-506 | LOW | UNDER-SCOPE | E (testing); baseline honesty | bare suite at HEAD `1 failed, 7080 passed, 3 skipped, 2 xfailed`; the failing node run alone; 7305 passed recorded at child 03's review | The plan named no suite baseline and no known failure, so an executor would meet an inherited red test and a pass total 225 lower than the last recorded one with nothing to attribute either to. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The validation section records the measured baseline, the known `reaskscore` failure by node id, and the 7305 -> 7080 move with its cause; E-05 and V-05 require identifying that failure by its NAMED plans rather than accepting the label; F-10 added. |
| PR-507 | LOW | IN-SCOPE | F (honest documentation) | `ipd_schema.VALIDATION_RESULTS` = `{pending, pass, blocked, failed}`; `_VALIDATION_RULES` requiring nonempty evidence for `failed`/`blocked`; `check_checkpoint`'s `pre-transition` branch; the seven-token absence scan over `evaluate_set_retirement` | OQ-01's rationale asserted a chain of mechanisms (a failing V-item is recordable, finalize refuses, retirement cannot proceed) without citing any of them, and omitted the honest gap that nothing PREVENTS an executor weakening a criterion instead. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 now cites each mechanism as verified from source and states the self-assessment gap explicitly, pointing at spec Section 3a limit 3 as the governing statement of that limit. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The probe test file already changed at HEAD. Fix the pin, or keep it and let the Set fail? | Fix the PIN: absence from the SET'S OWN diff, plus the seven functions at a re-derived AST span, plus the suite passing. | Keeping the byte pin and accepting a failure (rejected: it fails the Set's completion gate for work this Set did not do, and the honest reading of criterion 9 is "unedited BY THIS SET"). Reverting `75b90271` to restore the bytes (rejected absolutely: a shared-checkout violation, and the specific bad outcome this finding exists to prevent). Deleting the pin entirely (rejected: it is the durable form of the spec's own BLOCKER correction SR-001 and must keep catching a real substitution). | `git diff --stat a4808752 HEAD` on that path; the two commit timestamps; criterion 9's "passing UNEDITED" wording; the 476-line span and 96 passing tests measured at review | yes |
| D-2 | Should the Set's diff be computed as a range over main or as the union of the children's commits? | The UNION of the five children's commits. | A range over the Set's base commit (rejected on the measurement: a range includes every other party's merges, which is precisely how the byte pin came to fail, so the range would keep reporting third-party work as this Set's). | the `75b90271` merge sitting inside any plausible base..HEAD range while touching nothing this Set owns | yes |
| D-3 | Criteria 10 and 11 are child 03's. Drop them here, or keep them with a stated addition? | KEEP, narrowed to the post-migration inversion (a conforming queue reaching the probe) that child 03 structurally cannot observe. | Dropping them and citing child 03 (rejected: the conforming-queue case is genuinely unobserved by any sibling, and dropping it would leave the ordering half-proven). Keeping them as written (rejected: it is the duplication this plan's own deferral section forbids for six other criteria). | `0xmk4e` E-04/E-05 read at review; child 03 executing before child 04's migration, so its worktree contains no conforming orchestrator | yes |
| D-4 | How should the three real deliverable fixtures survive child 04's migration? | Embed them as LITERAL text in this child's own test file, with the git revision cited. | Reading the live plan files at test time (rejected: post-migration those files hold CONFORMING rows, so the test would assert the inverse of criterion 3, and it would also become a test of child 04's migration that breaks on any future edit). Reading them from git at test time (rejected as needless: it adds a git dependency to a unit test for text that is frozen by definition). | all three texts quoted from HEAD at review; child 04's Scope covering the pending-plans tree | yes |
| D-5 | Is the criterion-1 proof a grep for absence, or an accounted search? | An ACCOUNTED search: enumerate expected hits first, then account for every actual one. | A bare grep for absence (rejected on the measurement: two legitimate child-table scanners and three `RECOGNIZED_STATUS` references already exist, so absence is false today and the grep would read shipped design as a violation). | both scanners located at review with their docstrings; the three `RECOGNIZED_STATUS` sites | yes |
