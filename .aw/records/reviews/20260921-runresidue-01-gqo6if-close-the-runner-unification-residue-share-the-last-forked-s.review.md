# Review findings: plan gqo6if

- Subject-Id: gqo6if
- Subject-Type: ipd
- Reviewed-At: 2026-09-22
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `64c452fb` in an isolated review lane. The plan was committed and unmodified, so no
pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author` CONFORMED before revision
and `--phase review-finalize` conforms after (one `IPD-Z602` count advisory remains, which is the expected
consequence of the E-04 split below). `aw check` was also run and reported TWO error-severity findings the
IPD linter does not see; both are now clear and the tree total fell 59 -> 57.

THE PLAN IS WORTH DOING AND ITS ANCHOR IS SOLID, which matters because the findings below are numerous.
Re-verified independently: `reclaim_lanes_on_interrupt` really is copied code, at 0.998 normalised similarity
with IDENTICAL length on both sides at BOTH the plan's cited commit and review HEAD, so E-03 has a genuine
and well-chosen subject. The maintainer's test ("`oc_runipd` is the preferred version unless a difference is
a real capability, one host does A the other NOT A") is quoted accurately from `rununify`'s records. Spec
`c4gd2h` R19 says what F-06 claims. All 11 `rununify` children are `executed`. `aw research new` exists with
the `--kind/--slug/--apply` interface E-02 assumes. And the STRUCTURE that motivates the whole plan
reproduces exactly: the strict residue is a strict subset of the loose one with 12 to 13 symbols between
them, so no threshold resolves the question and a per-symbol decision is the right design.

EVERY HEADLINE NUMBER IS UNREPRODUCIBLE AT THE PLAN'S OWN CITED HEAD, which is a pointed finding because the
plan's stated purpose includes preventing exactly this (PR-001):

```text
                        authored      measured f763be8c      measured review HEAD
co-defined symbols      57            58 (57 fn + StallWatchdog)   58
one-side-delegates      5             1                            0
strict residue          7 / 170       25 / 444 agy unparse lines    23 / 391
loose residue           20 / 667      37 / 1103                     36 / 1122
reclaim_lanes... lines  174 each      68 each (unparse) / 252 span   98 each / 252 span
run_queue               456 ln/10 cl  161 unparse ln / 8 calls       161 / 8
```

The `57` silently excluded the class `StallWatchdog`, which the plan's own residue lists then also omit. The
strict and loose figures match NEITHER test at EITHER commit. The line discrepancies are metric confusion
(`ast.unparse` versus raw source span differ by 2.5x on these symbols), which is precisely the failure the
plan's own honesty rule warns about, one paragraph away from committing it.

TWO FINDINGS WOULD HAVE SENT AN EXECUTOR BACKWARDS AGAINST A RECENT MAINTAINER DECISION.

First (PR-003), E-05 directs the executor to extend `tests/test_rununify_characterization.py`. That file does
not exist, and neither does ANY `tests/*characterization*` file: commit `d4dd6b88` (2026-09-18) "test: retire
change-detector tests over code text and prose" deleted `tests/test_wtiso_characterization.py` (192 lines),
and `7ebc2964` deleted four `test_rununify_*_characterization.py` files totalling roughly 3,900 lines,
removing `len(getsourcelines(...))` pins, `SequenceMatcher` ratios and AST censuses. The plan was authored
three days later. Writing a new file of that form would revert a four-day-old decision, so E-05 now demands
observable-behavior pins through the public seam and FAILS a test containing a source-text or line-count
assertion even when green. This is the same bar `40it5e` E-03 was given at its own review.

Second (PR-005), E-03 says to "re-base any guard that pins it as forked". Read at review,
`tests/test_runner_refork_guard.py` cannot express what this plan builds: each `REFORK_TABLE` row requires
the runner to have NO top-level definition of the symbol AND to expose the OWNER'S OBJECT via `assertIs`,
and a "thin host-shaped shell" is a top-level definition that is not the owner's object, so it fails both
halves. Measured confirmation: `oc_runipd.integrate_lane_branch is runner_shared.integrate_lane_branch` is
False, and that symbol is correctly ABSENT from the table. The guard is for bare re-exports; a shell-bound
symbol needs a delegation pin instead. Baseline `17 passed`.

THE PLAN ALSO POINTED AT TWO SYMBOLS THAT ARE ALREADY UNIFIED (PR-002), which is the over-reporting failure
mode and the mirror of PR-001's under-measurement:

```text
reconcile_interrupted   oc=2  agy=2  sim=1.000  shared_oc=True  shared_agy=True
  both bodies: runner_shared.reconcile_interrupted(run_dir, state, save_state=save_state)
driver_finalize         oc=23 agy=22 sim=0.720  shared_oc=True  shared_agy=True
```

`reconcile_interrupted` is already the sanctioned delegation shape, so "unifying" it is a no-op that would be
reported as progress. `driver_finalize` is partially shared and is a judgement call for E-02, not an
unshared fork. Both were removed from the cluster lists, with `driver_finalize` allowed to re-enter only via
E-02's recorded decision.

E-04 WAS ALSO TOO LARGE, and the linter said so before I did (PR-007). One item covered 18 symbols across
four unrelated clusters with four independent test surfaces, which the right-sizing rule forbids outright. It
is now four items ordered LEAST-RISKY-FIRST, which is a deliberate inversion of the authored order: the
remainder cluster (prompts, recorders, flag registration) runs first because a mistake is immediately
visible; the lock/base cluster next because `run_lock` owns spec `c4gd2h` R2's observable release and a
regression strands a lock; `set_plan_approved` ALONE because it writes PERMANENT workflow history through a
per-host actor the `hostdedup` Set already measured as a misattribution hazard, so it needs a
both-directions attribution test; and the stop/signal cluster LAST because it is both the riskiest (it runs
when an operator interrupts) and the LEAST similar group measured (`install_stop_triggers` 0.493,
`_observe_between_turn_stop` 0.679, `_record_forced_stop` 0.693), making it the likeliest to hold a real
capability difference rather than duplication. That similarity spread is new information the authored plan
did not carry, and it is what justifies the ordering.

NOT FLAGGED, checked and correct: OQ-01 (wording-only differences are SHARED with the string injected) and
OQ-02 (a behavioral divergence is reported and left forked) are both well-reasoned, resolved from repository
evidence, and non-blocking, so neither gates the plan; the `HostLabels` precedent is real and correctly cited
as the mechanism rather than a second one being invented; the scope fence is in the DECLARATION form rather
than the forbidden "STOP and report" form; the gate already carried the honesty rule and the path-scoped
commit/never-push contract; and `Scope-Paths` correctly declares no `.spec.md` path for a pure extraction
(the two spec-adjacent clusters are now required to report rather than amend).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / E. Verification | Measured at BOTH `f763be8c` and review HEAD: co-defined 58 not 57; one-side-delegates 1 not 5; strict 25/444 then 23/391 not 7/170; loose 37/1103 then 36/1122 not 20/667; `reclaim_lanes_on_interrupt` 68 then 98 `ast.unparse` lines (252 span) not 174; `run_queue` 161 lines / 8 calls not 456 / 10 | EVERY HEADLINE FIGURE IS UNREPRODUCIBLE AT THE PLAN'S OWN CITED HEAD, in a plan whose stated purpose includes preventing that. The `57` silently excluded the class `StallWatchdog`; the line figures confuse `ast.unparse` with raw source span (a 2.5x difference on these symbols). Scope was pinned to the stale "7 strict / 13 between", which would under-cover the residue. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern, Scope, F-01/F-02/F-03 and the honesty rule now carry the re-measured figures at BOTH commits with the metric named; scope membership is defined as whatever E-01's scanner reports at execution HEAD; V-01 requires the metric and a reconciliation against these numbers. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness / G. Executability | `reconcile_interrupted` measured as a two-line byte-identical body on both sides delegating to `runner_shared.reconcile_interrupted` (sim 1.000); `driver_finalize` calls `runner_shared` on both sides (23/22, sim 0.720) | E-04 NAMED TWO ALREADY-UNIFIED SYMBOLS AS LIFT TARGETS, so an executor would "unify" code that is already one implementation and report it as progress. This is the over-reporting mirror of PR-001. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both removed from the cluster lists with the measured evidence recorded (F-09); a standing rule makes the scanner authoritative over the prose and requires any already-delegating name to be SKIPPED and NAMED; V-04/V-08 fail a lift of an already-delegating symbol. |
| PR-003 | BLOCKER | IN-SCOPE | D. Anti-regression / E. Testing | `ls tests/*characterization*` -> no such file; `git show --stat d4dd6b88` (2026-09-18, "retire change-detector tests over code text and prose") deleted `tests/test_wtiso_characterization.py`; `7ebc2964` deleted four `test_rununify_*_characterization.py` files | E-05 PRESCRIBED A TEST FORM THIS REPOSITORY DELIBERATELY RETIRED THREE DAYS BEFORE THE PLAN WAS AUTHORED, and the file it names does not exist. Following it would re-create source-text/similarity/AST pins under a new name, reverting a maintainer decision. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now requires OBSERVABLE-behavior pins through the public seam, forbids source-text/line-count/`SequenceMatcher`/AST-shape assertions, cites the LIVE precedent, and records the deletions so a later reader does not go looking; V-05 requires evidence the file contains no such assertion; a new Step-0 convention states the boundary against the "source-reading tests are work" ruling so the two are not confused. |
| PR-004 | MEDIUM | IN-SCOPE | C. Architecture / G. Executability | `40it5e` is `Status: reviewed` (not executed) and declares `tests/test_rununify_characterization.py` in its own `Scope-Paths`; this plan carries `Item-Dependencies: none`; `40it5e` F-08 records the same edge from the other side | E-05 PLANNED TO EXTEND A FILE ANOTHER PENDING PLAN OWNS AND HAS NOT CREATED. The authored fallback ("create it if that plan has not executed") makes two plans create and extend the same new file with no declared edge, so the runner's dependency-depth sort cannot order them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now writes into files this plan owns (the existing behavioral suites in `Scope-Paths`, or a newly named file it declares), and is explicitly forbidden from reaching into `40it5e`'s file; recorded as F-10. |
| PR-005 | BLOCKER | IN-SCOPE | D. Anti-regression / E. Testing | `tests/test_runner_refork_guard.py` `Owned`/`REFORK_TABLE` contract (no top-level definition AND `assertIs` the owner's object); measured `oc_runipd.integrate_lane_branch is runner_shared.integrate_lane_branch` -> False, that symbol correctly absent from the table; baseline `17 passed` | "RE-BASE ANY GUARD THAT PINS IT AS FORKED" IS NOT PERFORMABLE for this plan's design: the guard's rows cannot describe a thin host shell, since a shell is a top-level definition and is not the owner's object, so adding a row fails BOTH halves. An executor would either fail the suite or weaken an assertion the repository built deliberately. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now states the guard's actual contract, restricts new rows to bare re-exports, and requires a DELEGATION pin for a shell-bound symbol; V-03 requires the guard green with the chosen form stated and FAILS a new row for a shell-bound symbol; recorded as F-08 and as a Step-0 convention. |
| PR-006 | HIGH | UNDER-SCOPE | C. Architecture and operability | `aw check` rule `check.ipd-uncarried-obligation` (severity `error`) plus `check.lifecycle-transition-invalid` (error), both reported for this plan before revision | TWO DETERMINISTIC REPOSITORY ERRORS THE IPD LINTER DOES NOT SEE. All four `## Deferred / out of scope` rows named no durable carrier, so each obligation would vanish from `aw attention` when the plan finalized; and the `## Workflow history` lines were ordered `draft` ABOVE `to-review` in a newest-first section, so the derived event stream read as a backwards transition. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Each Deferred row carries a reasoned `- Carrier-Declined:` (sanctioned end state, already discharged, unnameable-in-advance with OQ-02 governing, and "this plan IS the carrier"); the history lines reordered and re-verified with `ipd_lifecycle.validate_transition` (`draft -> to-review` now `ok=True`). `aw check` now reports ZERO findings for this plan; tree total 59 -> 57. |
| PR-007 | HIGH | IN-SCOPE | G. Executability (right-sizing) | `aw ipd lint` `IPD-Z602` density advisory; E-04 as authored covered 18 symbols across 4 clusters; similarity spread measured per symbol (0.295 to 1.000) | E-04 BUNDLED FOUR UNRELATED CLUSTERS WITH FOUR INDEPENDENT TEST SURFACES into one item, which the right-sizing rule forbids and the linter flagged. It also ordered the work riskiest-first by accident: the stop/signal cluster, which runs when an operator interrupts a run and is the least similar group measured, sat in the same pass as prompt strings. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into E-04 (low-risk remainder), E-06 (lock/base, owning `c4gd2h` R2's observable release), E-07 (`set_plan_approved` alone, with a both-directions attribution test because it writes permanent history through a per-host actor) and E-08 (stop/signal last), ordered least-risky-first, with matching V-06/V-07/V-08, per-symbol similarity figures recorded, and `Highest E allocated` advanced to 08. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan's headline counts do not reproduce. Correct them in place, or leave them and rely on E-01's scanner to supersede them? | Correct them in place at BOTH commits with the metric named, AND make the scanner authoritative for scope membership. | (a) Leave the figures and let E-01 supersede them - rejected: the Scope section pinned coverage to "the 7 strict / the 13 loose" symbols, so a stale count would under-cover the residue and an executor could report false completion. (b) Replace them with review's numbers as the new fixed baseline - rejected: that reproduces the original defect one layer on, since the strict residue already moved 25 -> 23 between the two commits. (c) Ask the maintainer - rejected: this is a measurement, not a decision. | Measured at `f763be8c` and review HEAD with `ast.unparse` body classification; `rununify` PR-006 records the same class of unreproducible-figure failure | yes |
| D-2 | E-05 names a test file and form that no longer exist. Recreate the file, or change the form? | Change the form to observable-behavior pins and write them in a file this plan owns. | (a) Recreate `tests/test_rununify_characterization.py` in the characterization style - rejected: `d4dd6b88` and `7ebc2964` deleted every such file on purpose three days before this plan was authored, so this would revert a maintainer decision. (b) Keep the file name and make it behavioral - rejected: that file is `40it5e`'s declared deliverable and `40it5e` is not executed, so two plans would race to create it with no declared edge. (c) Drop the before-pins requirement - rejected: F-05's argument for them survives its stale figures, and the suite asymmetry is real. | `git show --stat d4dd6b88` / `7ebc2964`; `40it5e` `Scope-Paths` and its F-08; this plan's `Item-Dependencies: none` | yes |
| D-3 | E-04 is too large and the linter flagged its density. Split it, and in what order? | Split into four cluster items, ordered LEAST-risky first (remainder, lock/base, `set_plan_approved` alone, stop/signal last). | (a) Leave it as one item - rejected: four independent test surfaces in one pass is what the right-sizing rule forbids, and `IPD-Z602` flagged it. (b) Split but keep the authored order (stop cluster early) - rejected: measurement shows the stop cluster is both the riskiest by consequence and the least similar (0.493 to 0.895), so it belongs last, against the most accumulated evidence. (c) Split `set_plan_approved` into the lifecycle cluster with `driver_finalize` - rejected: `driver_finalize` is already partially shared (F-09), and `set_plan_approved` writes permanent history through a per-host actor, which is a distinct hazard deserving its own item and test. | Per-symbol similarity and line measurements at review HEAD; spec `c4gd2h` R2 and R19; the `hostdedup` Set's measured `FULL_AUTO_ACTOR` misattribution hazard | yes |
