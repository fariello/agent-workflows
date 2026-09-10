# Review: extract the run viewer artifact audit into one shared module, child 6ltz1y (Set auditshare)

- Subject-Id: 6ltz1y
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `b644a7c3`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0 findings)
before semantic review, and `--phase review-finalize` conformed after the revisions. The plan carries no
`- Blocks-Release:` and says so explicitly because backlog `onasuh` carries none.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this as a
near-self-review and worth less than an independent one.

THE CORE PREMISE HOLDS AND I VERIFIED IT BY SYMBOL. `find_artifact_file` and `audit_step_artifact` are
defined in `run_viewer.py` and consumed only there (three call sites) and in its tests; `doctor.py`,
`check_engine.py` and `cli.py` reference neither. The one-implementation argument is sound and both cited
precedents are real (`test_runner_refork_guard.py`'s object-identity assertions and
`evaluate_review_finding_escalation`'s shared-predicate docstring).

THE FINDING THAT MOST CHANGES THE PLAN IS THAT ITS HEADLINE DEFECT IS FALSE. The plan says an archived
plan "may already be invisible to the audit" because the hardcoded list names a nonexistent
`plans/archive` and cannot track sharding, and it asks E-06 to ASSERT that the old code could not find a
sharded plan. Measured and falsified: `plans_archive.py` writes MONTHLY `YYYYMM/` shards INSIDE the
terminal dirs, those dirs ARE in the hardcoded list, and the loop uses `rglob`, so I constructed
`executed/202608/20260801-setx-01-abc123-thing.ipd.md` and today's code FINDS it. The shards are monthly,
not weekly as the plan twice states. An executor following E-06 literally would have written a test that
fails. The real defect in its place is the TYPE SET: the list covers plans and specs only, so a `backlog`
record carrying the queried id6 returns `None`. That is latent for `aw runs` (its steps are plans) and is
exactly what a second consumer would meet, which is the honest case for dropping the hardcoded list.

THE SECOND HIGH FINDING IS THAT E-04 MAY NOT BE BUILDABLE AS WRITTEN, and the plan's own OQ-03 contains
the argument without applying it. Liveness is not computed by the audit and cannot be supplied from
tracked state: `StepSummary.is_live` is an INPUT set by `load_run_summary` from a run directory's PID and
lock holder, and the audit only passes it through. `doctor.py` reads no run records anywhere. So "make the
doctor consumer liveness-aware" means coupling a tracked-record sweeper to gitignored box-local state,
which is precisely the objection OQ-03 accepts as decisive against `aw check`. If it is decisive there it
needs an argument here rather than silence. E-04 now requires choosing among three routes and recording
the cost, and I deliberately did not choose for the maintainer: the cheap-looking route (b) risks
duplicating the already-shipped `IPD-M105`, which OQ-03 itself measured.

A SMALLER BUT USEFUL INVERSION on the substring question. The plan treats substring matching as a present
danger because a review record carries its subject's id6. Today it cannot bite, because the hardcoded list
never searches `reviews/`. It becomes live exactly when E-03 widens the type set, which reframes the exact
declared-`- Id:` rule as the thing that makes the widening safe rather than as general tidiness. A review
record also declares `- Subject-Id:`, not `- Id:`, so the exact rule skips it for free.

I ALSO CORRECTED TWO PIECES OF STALE ENVIRONMENTAL LORE the plan would have propagated. Its F-10 says
`tests/test_run_viewer.py` is environment-sensitive and instructs the executor to treat failures there as
environmental; that module was fixture-isolated on 2026-09-08 by `e167c9b3` and I measured `75 passed` in
the primary checkout AND `75 passed` in a fresh clone with ZERO run dirs, so a failure there is now a real
regression and the original instruction would have taught an executor to ignore one. And the suite
baseline is wrong in both halves: `1 failed, 5958 passed` failing at the reporting-contract parity test
(another party's gitignored `opencode-recovery/` tree), not `1 failed, 5648 passed` at
`test_orchestrator_retirement`, which passes.

VERIFIED CORRECT AND LEFT ALONE: the collision defect (`resolve` really does return both paths for a
duplicated id6, so the verdict is available), `_check_path_status`/`IPD-M105` as OQ-03 describes it,
`check_engine._receipt_is_live` as the fail-safe precedent, the `selectors.py` read-only fence and its
three-plan overlap, and OQ-01/OQ-02's reasoning, which needed no change.

Six findings, all FIXED in place, no deferrals. No new open questions: E-04's route choice is recorded as
a required execution decision with its costs rather than a new question, since the plan delivers value
under all three answers.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-B01 | HIGH | IN-SCOPE | Evidence accuracy; E. testing | `plans_archive.py:4` (monthly `YYYYMM/` shards INSIDE terminal dirs); `artifact_core.shard_for_date` -> `cleaned[:6]`; constructed `executed/202608/...` -> FOUND by current code | **THE HEADLINE DEFECT IS FALSE AND E-06 WOULD HAVE ASSERTED IT.** The plan claims archived plans may already be invisible and asks for a test proving the old lookup could not find a sharded plan. The shards live inside the terminal dirs that ARE in the hardcoded list and the loop `rglob`s, so a sharded plan is found today; the shards are also monthly, not weekly. The real defect is the TYPE SET (a `backlog` record returns `None`) | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern and E-03 restate defect one as the type set with the falsification recorded; E-06 and required-tests replace the shard assertion with a type-set fixture and keep the shard case as no-regression only; spec-sync forbids enshrining the false claim in the new docstring; new F-11, F-2 rewritten |
| PR-B02 | HIGH | IN-SCOPE | C. architecture; G. executability | `run_viewer.py:97` (`is_live` field), `:930` (`is_live=(holder != HOLDER_NONE)`), `:1090-1096`, `:510`, `:559`; zero `runs` references in `doctor.py`; the plan's own OQ-03 | **E-04 MAY NOT BE BUILDABLE AS WRITTEN, AND THE PLAN'S OWN OQ-03 HOLDS THE ARGUMENT.** Liveness is an INPUT derived from a run dir's PID/lock holder, not something the audit computes or a tracked-state caller can supply. `doctor.py` reads no run records, so a liveness-aware doctor rule requires coupling a tracked-record sweeper to gitignored state, the exact objection OQ-03 treats as decisive against `aw check` | C:Medium; U:Medium; S:Low; F:High; Overall:Medium | FIXED | Concern states the measurement; E-04 rewritten to require an explicit choice among (a) doctor reads run records, (b) tracked-only cannot-be-live, (c) no consumer this plan, each with its cost, plus the warning that (b) risks duplicating the shipped `IPD-M105`; V-04 requires the route and reasoning pasted; scope check adds the declared-but-unmodified acknowledgment for route (c); new F-12 |
| PR-B03 | MEDIUM | IN-SCOPE | Evidence accuracy; E. testing | `git log -S` -> `e167c9b3` "test: isolate run viewer fixtures" (2026-09-08); fresh clone with 0 run dirs -> `75 passed`; primary checkout -> `75 passed` | **F-10'S ENVIRONMENTAL-SENSITIVITY CLAIM IS STALE AND WOULD TEACH AN EXECUTOR TO IGNORE A REAL REGRESSION.** The plan says `tests/test_run_viewer.py` reads live repo state and its failures have been environmental. It was fixture-isolated two days before the plan was authored and now passes with zero run dirs | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-10 rewritten with the correction and the measurement; E-06 and required-tests instruct treating any failure there as a real regression; conventions updated; a Deferred entry notes plan `utwr6y` still proposes this conversion and must not be pulled in |
| PR-B04 | MEDIUM | IN-SCOPE | E. testing; Evidence accuracy | bare pytest at `b644a7c3` -> `1 failed, 5958 passed, 3 skipped, 2 xfailed` at `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`; `test_orchestrator_retirement.py` -> `112 passed` | **THE SUITE BASELINE IS WRONG IN BOTH HALVES AND NAMES A TEST THAT PASSES.** The real failure is the reporting-contract parity test, caused by another party's gitignored `opencode-recovery/` transcript tree. An executor could read it as their own regression or clean up files that are not theirs | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 and required-tests carry the re-measured baseline, the real node id, the cause, a do-not-touch prohibition under the shared-checkout rule, and node-id rather than count comparison; V-06 requires both node-id lists; new F-15 |
| PR-B05 | MEDIUM | IN-SCOPE | C. architecture; G. executability | `selectors.py:397` `_iter_paths(repo_root, record_type)`; `:497-504` `resolve(repo_root, record_type, selector)` | **"CONSUME THE RESOLVER" IMPLIES AN ALL-TYPES CALL THAT DOES NOT EXIST.** Both entry points take ONE record type, so cross-type coverage means either passing the type the caller knows or looping the vocabulary and defining precedence across types. Unstated, this is where an executor either silently narrows the lookup or invents precedence | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 names the catch and requires the choice be stated; V-03 requires the cross-type method pasted; new F-14 |
| PR-B06 | MEDIUM | IN-SCOPE | A. correctness; B. security lens on matching | constructed review-collision case (the hardcoded list never searches `reviews/`); the reviews convention (`- Subject-Id:`, not `- Id:`) | **THE SUBSTRING RISK IS INVERTED: it is latent today and is CREATED by E-03's own widening.** Today's loop cannot return a review record because `reviews/` is never searched. Widening the type set is what makes substring matching dangerous, so the exact rule is what makes the widening safe, not a general improvement | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 reframed with the measurement and the `- Subject-Id:` reason the exact rule skips reviews for free; V-03 requires that reasoning stated; new F-13 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan's headline defect (shard blindness) is false (PR-B01). Drop defect one entirely, or replace it? | REPLACE IT with the measured TYPE-SET defect, and record the falsification explicitly so the executor does not chase it | Drop defect one and justify the extraction on collision alone (rejected: the hardcoded list IS a real limitation, just not the one claimed, and dropping it would understate why the private walk must go); keep it with a caveat (rejected: E-06 asks for an assertion that would FAIL, so a caveat is not enough) | monthly shards inside terminal dirs + `rglob`; constructed sharded plan FOUND; constructed backlog record -> `None` | yes |
| D-2 | E-04's liveness requirement may be unbuildable without new coupling (PR-B02). Pick a route, or put it to the maintainer? | REQUIRE AN EXPLICIT RECORDED CHOICE among three routes with costs, and do NOT pick one in review | Choose (a) doctor reads run records (rejected: it contradicts the plan's own accepted OQ-03 reasoning about run-record dependence, and that tradeoff is the maintainer's); choose (c) drop the consumer (rejected: that guts the item's actual request, `onasuh` asked for doctor to see this); leave E-04 as authored (rejected: it assumes an input that does not exist on the doctor side) | `is_live` sourced from PID/lock holder; zero run-record reads in `doctor.py`; OQ-03's accepted objection; `IPD-M105` already ships the tracked-only predicate | yes |
| D-3 | Should this review fix `tests/test_run_viewer.py`'s stale F-10 claim only, or note the overlap with plan `utwr6y`? | CORRECT F-10 AND NOTE THE OVERLAP in Deferred, without touching `utwr6y` | Silently correct F-10 (rejected: `utwr6y` proposes exactly this conversion and an executor of THIS plan seeing the corrected fact might helpfully do it, which is scope theft from another plan); edit `utwr6y` here (rejected: it is not this review's target and not in this plan's scope) | `e167c9b3`; `75 passed` in a fresh clone with 0 run dirs; `utwr6y`'s scope | yes |
