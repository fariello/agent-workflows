# Review: require a durable carrier for an unfixed defect an IPD names, child rnkqrc (Set durablecapture)

- Subject-Id: rnkqrc
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `32948d10`. Structural preflight `aw ipd lint --phase author` CONFORMED with zero findings
before semantic review; `--phase review-finalize` after the revisions reports only the deliberately-open
blocking question (`IPD-Q501` on the new OQ-05), which is the correct fail-closed state rather than an
unrepaired structural defect. No product code was modified by this review.

DISCLOSURE: the plan was authored by the same model family, so this is close to a self-review and is worth
less than an independent one. Its value therefore rests on what was EXECUTED. Sixteen things were run: the
`H_DEFERRED` and `From-Backlog` greps over `ipd_lint.py`; the `H_DEFERRED` declaration and both H2 orders in
`ipd_schema.py`; `open_question_error`'s body; the `OQ_FIELDS` comment block; `attention.py`'s
`executed -> done` mapping; `CloseVerdict` and `evaluate_blocking_close` read in full; the
`review-finding-unescalated` evaluator docstring; `config.dependency_cutover_date` evaluated against this
repository; `parse_item_dependencies` evaluated on four dependency tokens; the corpus plan count, its
disposition split, and a section-scoped count of deferred rows; the carrier-field grep; `lint_text`'s purity
contract and the `check_checkpoint` call path; `_merge_review_escalation`'s placement docstring; the CI
workflow's plans-fail-closed and backlog-advisory steps; `b7xarm`'s front matter and E-06; and the bare
suite.

EVERY DEAD-CODE CLAIM IS TRUE AND I RE-RAN ALL OF THEM. `rg -c H_DEFERRED agent_workflows/ipd_lint.py` exits
1 with zero matches while `ipd_schema.py:48` declares the heading and `:70`/`:86` place it in BOTH the child
and orchestrator H2 orders, so the section really is mandatory and its contents really are never read.
`rg -c From-Backlog agent_workflows/ipd_lint.py` likewise exits 1. `open_question_error`
(`ipd_schema.py:1340-1354`) really does accept any non-empty rationale and its docstring really does say
"Semantics are the reviewer's job". `OQ_FIELDS` (`:1315-1329`) really is declared-and-never-read with that
fact written into the comment, including the standing warning about a future closed allowlist.
`attention.py:1246` really maps `executed` to `done`. The precedents are correctly identified and their
documented semantics are exactly as described, including `CloseVerdict`'s three named paths. This is careful,
well-sourced work and I weakened none of it.

THE FINDING THAT DECIDES WHETHER THE PLAN IS EXECUTABLE AS SCOPED IS PR-301, AND THE SIBLING'S OWN REVIEW
FOUND IT FIRST. This plan's history instructs E-02 to read the normalized defect report that `b7xarm` E-06
persists on the run record, because that record is the only thing distinguishing "found nothing" from "never
asked". That read is not reachable from the declared scope: the record lives under `.aw/records/runs/`, which
is gitignored with zero tracked files, and none of the four declared `Scope-Paths` contains any reference to
that tree. `b7xarm`'s round-1 review reached the identical conclusion independently and recorded it as its
PR-A05, and amended its E-06 to write the record's location and shape down so this plan's executor would
have a contract. The resolution changes what this plan builds and possibly what it declares, so it is
escalated as blocking OQ-05 with three costed options rather than decided.

THE PLAN CONTRADICTS ITSELF ABOUT ITS OWN DEPENDENCY, AND THE PROSE HALF NAMES AN EDGE THAT DOES NOT EXIST.
The front matter declares `Item-Dependencies: executed:b7xarm`; OQ-04's prose says the plan "now declares
`Item-Dependencies: to-review:b7xarm`". Evaluated: `parse_item_dependencies('to-review:b7xarm')` is rejected
outright with "expected executed:/exists:/state:", as are `reviewed:` and `approved:`, while
`executed:b7xarm` parses to a single well-formed edge. So the front matter is right, the prose is wrong, and
anyone who had trusted the prose would have written a statement the dependency linter refuses. `executed:` is
also the correct semantics given the maintainer's ruling that the declaration must be produced before the
check is built.

THE BLAST RADIUS IS LARGER THAN F-6 STATES AND THE PLAN COUNTED THE WRONG THING. F-6 says 530 plans;
measured 608. More importantly the unit that will generate findings is the deferred ROW, not the plan: 476
plans carry at least one `## Deferred / out of scope` bullet, 1929 rows in total, and all 104 pending plans
carry rows, 714 of them. Zero plans anywhere carry a typed carrier field. So a per-row error rule fires 714
times on the tree that is actually being worked, which makes E-05's staged severity load-bearing rather than
cautious, and makes the prose-only refusal case the corpus NORM rather than a contrived fixture.

E-03 CANNOT BE IMPLEMENTED WHERE IT SAYS, FOR A REASON THE REPOSITORY HAS ALREADY WRITTEN DOWN TWICE. The
`pre-transition` checks live in `check_checkpoint`, which is called from `lint_text`, whose contract is "Pure:
no I/O". Resolving a carrier against the backlog and plan trees is I/O, so the rule must be merged in
`lint_file`, exactly as the Item-Dependencies resolution checks and `_merge_review_escalation` already are;
that latter docstring says its placement "is load-bearing" for precisely this reason. The corollary is that a
text-only lint cannot report the rule, which is intended and already asserted for the sibling rule.

THE CUTOVER MECHANISM E-05 PROPOSES TO REUSE IS UNSET IN THIS REPOSITORY. `config.dependency_cutover_date`
returns `None` here, and an absent marker is the documented grandfather-everything case, so naive reuse would
leave the `error` tier unreachable and the rule would ship as warn-only while its own test appeared to pass.
Three options are now recorded, and V-05 must show an actual erroring new plan rather than asserting one.

Also corrected: both precedent citations drifted by roughly 29 lines; the gate paragraph claimed "OQ-01 is
open but Blocking: no" when OQ-01 is resolved and the blocking questions are OQ-04 and the new OQ-05; and the
required-tests note attributes ~14 failures to a module that is green today, while the real environmental
failure is the reporting-contract parity test caused by another party's gitignored tree.

Ten findings. Nine FIXED in place, one escalated as a blocking open question. No deferrals. E-items and
V-items unchanged at six each, bijection intact.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | BLOCKER | IN-SCOPE | C. architecture; scope discipline | `rg 'records/runs\|state_root\|run_dir'` over `check_engine.py`/`ipd_lint.py`/`ipd_schema.py` -> no match; `git ls-files .aw/records/runs` -> 0; `b7xarm` E-06 and its PR-A05 | **THE RUN-RECORD READ THE PLAN'S OWN HISTORY MANDATES IS NOT REACHABLE FROM ITS DECLARED SCOPE.** E-02 is told to read `b7xarm`'s normalized report, which is the only thing distinguishing "found nothing" from "never asked", but that record lives in a gitignored tree no declared module references. `b7xarm`'s own review found the same gap. Either a reader must be added and declared, or the plan must state that it enforces a strictly weaker rule | C:Medium; U:Low; S:Low; F:High; Overall:Medium | OPEN | ESCALATED as OQ-05 (`Blocking: yes`, `Finding: PR-301`) with three costed options and a recommendation. E-02 gated, Under-scope records the honest limit, proposed-changes gains a step 0, gate updated. NOT decided: option (a) re-scopes a release-gated plan and couples `check_engine` to run state; option (c) changes release sequencing |
| PR-302 | HIGH | IN-SCOPE | A. correctness; evidence accuracy | `parse_item_dependencies` evaluated on `executed:`/`to-review:`/`reviewed:`/`approved:` + `b7xarm`; front matter `:10` versus OQ-04 prose | **THE PLAN CONTRADICTS ITSELF ON ITS DEPENDENCY AND THE PROSE NAMES AN ILLEGAL EDGE.** Front matter says `executed:b7xarm`; OQ-04 prose says `to-review:b7xarm`, which the parser REJECTS ("expected executed:/exists:/state:"). Anyone copying the prose would have failed the dependency linter, and `executed:` is also the semantically correct edge given the maintainer's ruling | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | OQ-04 prose corrected with the measurement, the front-matter value affirmed as authoritative, and `b7xarm`'s current `reviewed` status noted so the unmet edge is understood as intended. New F-12 |
| PR-303 | HIGH | IN-SCOPE | E. testing; C. operability | `ls .aw/records/plans/*/*.ipd.md \| wc -l` -> 608; section-scoped row count -> 476 plans / 1929 rows, pending 104 plans / 714 rows; `rg '^- Carrier:'` -> 0 | **THE BLAST RADIUS IS 15% LARGER IN PLANS AND UNCOUNTED IN ROWS**, and rows are the unit that generates findings. All 104 pending plans carry deferred rows and none carries a carrier field, so a per-row error rule fires 714 times on the working tree. F-6 measured plans only and understated both | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-6 re-measured and raised to HIGH with the row denominator; E-05 and V-05 require counts per plan AND per row; E-06 notes the prose-only case is the corpus norm; the gate paragraph carries the corrected numbers. New F-6 text |
| PR-304 | HIGH | IN-SCOPE | A. correctness; C. architecture | `ipd_lint.py:754` (`check_checkpoint`), `:1066` (called from `lint_text`), `:1040` ("Pure: no I/O"), `:1173-1191` (`_merge_review_escalation` placement docstring) | **E-03 CANNOT BE IMPLEMENTED WHERE IT SAYS: the `pre-transition` checks live in a PURE function that may not do I/O**, while carrier resolution requires reading the backlog and plan trees. The repository has already moved two such checks to `lint_file` and written down why. E-03 gave no seam, so a faithful executor would have put the predicate in the pure path or abandoned resolution | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-03 now names `lint_file`, mirrors `_merge_review_escalation`'s shape (checkpoint frozenset, skip legacy/quarantined, reuse the parsed doc, delegate to one evaluator), states the `lint_text`-cannot-report corollary, and requires the deliberate divergence from `_REVIEW_ESCALATION_CHECKPOINTS` to be documented in place. V-03 and E-06 require that corollary proven. New F-10 |
| PR-305 | MEDIUM | IN-SCOPE | C. operability; E. testing | `config.dependency_cutover_date(Path('.'))` -> `None`; `check_engine.py:2439`; `oc_runipd.py:2544` | **THE CUTOVER MECHANISM E-05 REUSES IS UNSET HERE, so naive reuse ships warn-only forever** while the test appears to pass. An absent marker is the documented grandfather-everything case, so the `error` tier would be unreachable until someone sets a date | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 records the measurement and offers three explicit options (reuse and say so, a separate marker, or gate on the plan's own `- Date:`); V-05 requires the chosen option named and the marker value pasted if reused. New F-11 |
| PR-306 | MEDIUM | IN-SCOPE | G. executability | the gate paragraph versus OQ-01 (`Status: resolved`) and OQ-04 (`Blocking: yes`, `Status: resolved`) | **THE GATE PARAGRAPH NAMES THE WRONG QUESTION AS THE LIVE ONE.** It says "OQ-01 is open but `Blocking: no`"; OQ-01 was resolved by the maintainer on 2026-09-08, and the questions carrying `Blocking: yes` are OQ-04 (resolved, blocking retained for sequencing) and now OQ-05 (genuinely open). A reader would look for a decision in the wrong place | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate paragraph corrected to name both blocking questions, distinguish the resolved-but-blocking sequencing case from the genuinely open one, and direct that OQ-05 be answered first |
| PR-307 | LOW | IN-SCOPE | Evidence accuracy | `check_engine.py:1963` (`CloseVerdict`), `:1980` (`evaluate_blocking_close`); plan cited `:1934`/`:1951` | **BOTH PRECEDENT CITATIONS DRIFTED by about 29 lines** in a plan whose central instruction is "mirror this shape". The symbols and semantics are otherwise exactly as described | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 carries the corrected anchors and enumerates `CloseVerdict`'s five fields, noting that `severity` and `fixes` are what E-05 and the operator message need. V-02 cites the corrected lines. New F-13 |
| PR-308 | LOW | IN-SCOPE | E. testing | bare pytest -> `1 failed, 5958 passed, 3 skipped, 2 xfailed`; `tests/test_run_viewer.py` green; `.gitignore:49`; backlog `8kttqq` | **THE TEST NOTE EXCUSES FAILURES IN A MODULE THAT PASSES TODAY**, which would let an executor dismiss a real regression. The genuine environmental failure is the reporting-contract parity test caused by another party's gitignored tree | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required-tests and V-06 carry the re-measured baseline, the real node id and cause, a do-not-touch prohibition per the shared-checkout rule, and a node-id comparison; the stale attribution is marked stale. New F-14 |
| PR-309 | MEDIUM | UNDER-SCOPE | E. testing; D. anti-regression | `git ls-files .aw/records/runs` -> 0; `b7xarm` E-06's tmp_path requirement; `rbftpl`'s recorded trap | **E-06 NEVER SAYS WHERE ITS FIXTURES LIVE**, and the carrier cases require real tree structure (a `backlog/open/` item, a `plans/pending/` plan, a `plans/executed/` plan). A test built against the live trees would be non-deterministic and would break in CI and in every lane worktree, which is the trap `rbftpl` already recorded and `b7xarm` already guards against | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 requires every carrier target built under tmp_path and forbids reading the live trees; V-06 requires that confirmed |
| PR-310 | LOW | IN-SCOPE | C. architecture | `ipd_lint.py:1167-1170` (`_REVIEW_ESCALATION_CHECKPOINTS` excludes `pre-transition` because "blocking there would only strand a completed plan") | **THIS PLAN DELIBERATELY INVERTS A DOCUMENTED SIBLING DECISION AND SAYS NOTHING ABOUT IT.** The review-escalation rule excludes `pre-transition` on purpose; this rule targets it on purpose. Both are defensible, but an undocumented divergence invites a later reader to "fix" one to match the other | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 requires the tension stated in a comment beside the new checkpoint set, with the reason this rule is the exception (the transition is the moment the obligation would vanish); V-03 requires that comment pasted |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The run-record read is unreachable from the declared scope (PR-301). Pick a resolution, or escalate? | Escalate as blocking OQ-05 with three costed options and a recommendation of option (b) | Choosing (a) and adding a reader plus scope path myself; choosing (b) and narrowing the plan myself; marking it a mere paperwork fix and leaving it non-blocking | Option (a) re-scopes a release-gated plan and creates a new dependency direction (`check_engine` reading run state) that nothing in that module does today; option (c) changes release sequencing. Both are maintainer calls. Leaving it non-blocking was rejected because the plan's history actively INSTRUCTS the unreachable read, so an executor would either add an undeclared reader or silently drop the ruling's central distinction | yes |
| D-2 | The plan's dependency prose names an illegal edge while its front matter is correct (PR-302). Fix which? | Correct the prose to match the front matter, and affirm `executed:` on the merits | Changing the front matter to match the prose; leaving both and noting the discrepancy | Measured: `to-review:b7xarm` is rejected by `parse_item_dependencies`, so the prose value cannot exist in a conforming plan. `executed:` is also semantically right, since the maintainer's ruling requires the declaration to be PRODUCED first and a merely-reviewed `b7xarm` produces nothing | yes |
| D-3 | E-05's cutover reuse is unset here (PR-305). Mandate one boundary mechanism, or offer options? | Offer three explicit options and require the choice stated and demonstrated | Mandating reuse of `dependency_schema_cutover`; mandating a new marker; mandating the `- Date:` comparison | Mandating reuse would ship a rule whose error tier is unreachable while its test passes, which is the worst outcome; mandating a new config surface pre-empts a design choice the executor is better placed to make with the code in front of them. What was NOT acceptable was silence, since the plan asserted staged severity works without checking whether the mechanism was configured | yes |
| D-4 | Is the expired/incorrect detail in this plan (PR-302, PR-303, PR-307) grounds for REPLAN? | No: REVIEWED - OPEN QUESTIONS with revisions applied | REJECT - NEEDS REPLAN | Every load-bearing premise re-verified TRUE (all five dead-code findings, both precedents, the attention mapping). The corrections are numbers, citations and one contradictory sentence, plus two implementation seams that bounded edits supplied. Only the OQ-05 scope question genuinely needs an answer, and E-01 is valid under either | yes |
| D-5 | Should the reviewer fix the environmental suite failure (another party's gitignored `opencode-recovery/` tree)? | No: record it, name the cause and tracking item, forbid touching it | Deleting the tree; adjusting the parity test's expected set | It is another party's gitignored session transcripts in a shared checkout, which the shared-checkout rule forbids cleaning up; it is already tracked as backlog `8kttqq` (`open`); and it is outside both this plan's `Scope-Paths` and a review's authority, since reviews change plans and not code | yes |

## Round 2

Round 2 exists ONLY to close the finding(s) below, whose escalated question(s) the maintainer answered on
2026-09-10. It re-critiques nothing: every other round-1 finding was already `FIXED` and is superseded
unchanged.

WHY IT IS NEEDED: the escalation contract (`plan-review.md:335-341`) defines the path INTO a blocking
question and no path back, so an answered question leaves its finding reading `OPEN` forever while
`subject_gating_blocks` keeps refusing the plan on a decision that has been made. Appending a round is
the sanctioned mechanism, since `ReviewDocument.current_findings` reads only the LAST round
(`review_findings.py:236-243`). This is the SECOND such cleanup in one session; the durable fix is plan
`qhy3i3` E-07, which is authored and awaiting approval.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | BLOCKER | IN-SCOPE | C. Architecture (unreachable read as scoped) | plan OQ-05 (`- Status: resolved`, `- Finding: PR-301`) | Carried forward from round 1 and now CLOSED by a NARROWER AND STRONGER ruling than the finding contemplated. Round 1 found the plan's history instructs the predicate to read a normalized report on the run record, which no declared scope path can reach (0 tracked files under `.aw/records/runs/`). Ruling of 2026-09-10, verbatim: "All defects require one or more backlogs or plans to address. The report is not needed. A backlog item or IPD is. This is a MUST, not a should." | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Closed on the maintainer's decision, which rejected the compromise offered rather than choosing it: the run-record read is DROPPED AS UNNECESSARY, not deferred, so no follow-up item is owed. The plan already builds the ruling, since E-02's HANDOFF escape requires a carrier resolving to a `backlog/open/` item or a non-terminal plan and explicitly rejects one resolving into `executed/`. Recorded that E-05's staged severity is a ROLLOUT mechanism whose end state is `error`, and that the plan's own history instruction to read the report is SUPERSEDED. |
