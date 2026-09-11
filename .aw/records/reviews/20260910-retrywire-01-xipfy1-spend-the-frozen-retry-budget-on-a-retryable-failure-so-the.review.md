# Review: spend the frozen retry budget on a retryable failure, child xipfy1 (Set retrywire)

- Subject-Id: xipfy1
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `09beb137`. Structural preflight `aw ipd lint --phase author` reported exactly one finding,
the expected `IPD-Q501` (OQ-01 blocking and open), before semantic review; `--phase review-finalize` after the
revisions reports the same rule for the two blocking questions that remain open, which is the correct
fail-closed state and not an unrepaired structural defect. No product code was modified by this review.

DISCLOSURE: the same model family authored the plan, so this is close to a self-review and is worth less
than an independent one. Its value therefore rests on what was EXECUTED rather than re-read. Eleven things
were run: the `ledger.jsonl` search across all run directories; the store-reference grep on both drivers;
an import scan of both drivers for `run_engine`; the frozen-budget read out of three real `state.json`
files; the bare suite; `tests/test_orchestrator_retirement.py` alone; the `tests/test_run_viewer.py` header
and its test count; the guard-module contents for both named test files; the oc-to-agy import enumeration;
`wyw936`'s and `1bfppy`'s and `r2i1b1`'s front matter; and spec `25kzda` Sections 2.1, 5.3 and 5.5.

MOST OF THE PLAN'S GROUNDWORK IS CORRECT AND I WEAKENED NONE OF IT. The dormancy claim holds exactly as
stated (both spending helpers appear only in their own module and one test file). The frozen budget really
is on disk and read by nothing, which I confirmed independently: `options.retry_budget: 2` in each of the
three newest run directories. `0` really is a legal budget with a documented falsy-check hazard. The
repository-policy tier really is deliberately absent, and the plan correctly refuses to add it. The
`failed-safely` conflation with a deliberate operator stop is real and is exactly the right reason to make
E-01 an allowlist rather than a denylist. The cost argument for a default of 2 is sound and correctly
sourced. This is careful work.

THE FINDING THAT DECIDES WHETHER THE PLAN IS EXECUTABLE AT ALL IS PR-001, AND THE PLAN DOES NOT KNOW ABOUT
IT. `plan_retry` and `retry_budget_remaining` are not free functions over a run's `state.json`: both take a
`run_engine.RunEngine` as their first positional argument and immediately call `engine.reconstruct_state()`,
and `RunEngine` requires a `RunLedgerStore` over a hash-chained `ledger.jsonl`. No driver run has one,
measured three independent ways (0 `ledger.jsonl` files across 143 run directories; zero
`run_ledger_store`/`RunLedgerStore` references in either driver; neither driver imports `run_engine` at
all), corroborated by spec `25kzda:28` conceding "the ledger is built but UNWIRED" and by sibling plan
`i1hlgx` which exists solely to make that gap honest to operators. The state vocabularies are disjoint
too: `plan_retry` raises `NoRetryableStateError` for any step not in `STATE_FAILED`/`STATE_BLOCKED`, and a
driver queue item never holds either value. So E-03's instruction, "spend the budget through the shipped
helpers, in `oc_runipd.py`/`agy_runipd.py`, and do not reimplement any of it", has NO executable form in
the declared `Scope-Paths`. An executor would have completed E-01 and E-02, then discovered there is no
engine to pass and nothing that constructs one.

I DID NOT RESOLVE THAT MYSELF, AND THE REASON IS THE POINT. The three available shapes are: wire the
drivers to a ledger first (depends on unowned work), spend the budget in the drivers' own substrate
(a second implementation of semantics this plan's own E-03 forbids duplicating), or narrow the plan to the
engine-side callers where an engine does exist (does not fix the operator-visible symptom in the plan's
own Concern, since `--retry-budget` is a driver flag). Each is a scope-and-priority call, and shipping the
second is irreversible in the sense that other code starts depending on the duplicate. Two other plans
explicitly decline to decide this same question. So it is escalated as OQ-03 with `Blocking: yes`, which
makes the lint gate refuse execution at every checkpoint until a human answers.

FOUR OF THE PLAN'S CLAIMS WERE MEASURED FALSE AND ARE CORRECTED IN PLACE. First, OQ-01's premise expired:
`wyw936` is `graduated`, not `open`, and is owned by `1bfppy` (`reviewed`, `go-pending-approval`), so the
question collapses from "absorb a sibling's scope or ship a known hole" into an ordering choice between two
reviewed plans. Second, the suite baseline is wrong in both halves and blames a test that passes: the real
figure is `1 failed, 5958 passed, 3 skipped, 2 xfailed`, the failure is the reporting-contract parity test
caused by ANOTHER party's gitignored `opencode-recovery/` tree of 1746 session transcripts, and
`test_orchestrator_retirement.py` is `112 passed`. That one matters beyond bookkeeping: an executor holding
the stated baseline could read a co-worker's artifacts as their own regression and delete files that are not
theirs. Third, E-06 cites a header as documenting "23 tests" that fail in a fresh checkout; the rule is real
and worth keeping, the number appears nowhere in that file. Fourth, E-07 names a guard that polices
something else entirely, and its "no new cross-driver import" bar is unmeasurable as written because
`agy_runipd` already imports from `oc_runipd` at four module-level sites plus several function-level ones.

THREE MORE GAPS, EACH ONE AN EXECUTOR WOULD HAVE HIT MID-PASS. E-04's evidence-invalidation seam exists and
is INSIDE `plan_retry` itself, appending a `correction` record carrying `invalidates_seq`, so its
"locate it or stop" instruction is answered and the answer is engine-side, which is PR-001 from a second
direction. E-05's read-surface requirement is tighter than "per-item state": the diagnostics renderer reads
one specific FIELD NAME for exactly three statuses, so a reason under any other key renders nowhere even
when the state carries it, and budget exhaustion cannot introduce a new status because `observe_ledger`
declares a run incoherent on any value outside the closed set. And two of E-06's six boundary cases are
already green before any change, so presenting all six as proving the wiring would overstate the evidence.

Nine findings. Seven FIXED in place, two escalated as blocking open questions. No deferrals. E-items and
V-items unchanged at seven each, bijection intact; the plan's structure was strengthened, not enlarged.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | C. architecture; G. executability | `run_recovery.py:269-277`, `:415-417`, `:295-303`; `run_engine.py:117-127`; `find .aw/records/runs -name ledger.jsonl` -> 0 across 143 dirs; `rg -c 'run_ledger_store\|RunLedgerStore'` on both drivers -> no match (exit 1); neither driver imports `run_engine`; spec `25kzda:28`; `oc_runipd.py:317-334` | **THE PLAN'S CENTRAL MECHANISM CANNOT BE PERFORMED IN THE DECLARED FILES.** Both helpers require a `RunEngine` over a hash-chained `ledger.jsonl`; no driver run has one, neither driver imports `run_engine`, nothing constructs a store, and the two state vocabularies are disjoint (`STATE_FAILED`/`STATE_BLOCKED` versus `failed-safely`/`partial`/`interrupted`). E-03's "spend through the shipped helpers, do not reimplement" therefore has no executable form in `oc_runipd.py`/`agy_runipd.py`, and an executor would discover it only after E-01 and E-02 | C:High; U:Low; S:Low; F:High; Overall:High | OPEN | ESCALATED as OQ-03 (`Blocking: yes`, `Finding: PR-001`) with three fully costed shapes and a recommendation, because choosing one is a scope/priority decision two other plans explicitly refuse to make and one option is irreversible. Concern, E-03, E-04, V-03, proposed-changes step 0, scope check and the gate all now carry the gate. NOT resolved on reviewer authority |
| PR-002 | HIGH | IN-SCOPE | G. executability; evidence accuracy | backlog `wyw936` `- Status: graduated`; `1bfppy` front matter `:17-25` (`reviewed`, `go-pending-approval`, `From-Backlog: wyw936`) | **OQ-01 IS BUILT ON AN EXPIRED PREMISE AND OVERSTATES THE MAINTAINER'S DILEMMA.** It was authored on the finding that `wyw936` is "still `open` with no plan", which made its own recommended option (a) impossible and left the maintainer choosing between absorbing unowned scope and shipping a known hole. `wyw936` is now `graduated` and owned by a reviewed, approvable plan, so option (a) exists and option (c) is dead | C:Low; U:Low; S:Low; F:Medium; Overall:Low | OPEN | Question REWRITTEN with the re-measured state, two live options instead of three, a corrected recommendation, and an explicit note that it is a sequencing preference rather than a correctness gate. Left `Blocking: yes` because the sequencing choice is the maintainer's; `- Finding: PR-002` added. New F-15 |
| PR-003 | HIGH | IN-SCOPE | E. testing; D. anti-regression | bare `python3 -m pytest` at `09beb137` -> `1 failed, 5958 passed, 3 skipped, 2 xfailed in 54.60s`, failing `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`; `tests/test_orchestrator_retirement.py` -> `112 passed`; `.gitignore:49`; 1746 files in `opencode-recovery/` | **THE STATED SUITE BASELINE IS WRONG IN BOTH HALVES AND BLAMES A TEST THAT PASSES.** The plan claims `1 failed, 5648 passed` with a known `test_orchestrator_retirement` failure; that file is fully green and the count is 310 low. The real failure is the reporting-contract parity test, tripped by ANOTHER party's gitignored session-transcript tree. An executor holding this baseline could attribute a co-worker's artifacts to their own change, or "clean up" files that are not theirs, which the shared-checkout rule forbids | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required-tests carries the re-measured summary, the real node id, the cause, an explicit prohibition on deleting or fixing another party's gitignored tree, and a NODE-ID comparison replacing the count comparison. V-07 requires the failing node-id list, not just the summary line. New F-16 |
| PR-004 | HIGH | IN-SCOPE | G. executability; A. correctness | `tests/test_runner_item_dependencies.py:1552-1613` (dependency-regex guard), `:1616-1630` (why an oc-owned symbol cannot go in `REFORK_TABLE`); `tests/test_runner_refork_guard.py:262-336`; `agy_runipd.py:273`, `:315`, `:340`, `:1385`, `:2310`, `:2319`, `:2326`, `:2338` | **E-07 NAMES THE WRONG GUARD AND SETS A BAR THAT UNMODIFIED CODE ALREADY FAILS.** `AntiDivergenceGuardTests` polices private dependency regexes, not cross-host identity; the identity guard is `test_runner_refork_guard.py`'s `REFORK_TABLE`. Separately, `agy_runipd` already imports from `oc_runipd` at four module-level sites plus several function-level ones, so "gained no new import from `oc_runipd`" asserted as an absence is simply false and any such test would fail before the change | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-07 now names the correct guard and its identity assertion, points at the comment explaining which of the two tables is the legal home for a given owner, and converts the import bar into a COUNTED before/after delta. V-07 requires the table row, its justification, and both counts pasted. New F-14 |
| PR-005 | MEDIUM | IN-SCOPE | A. correctness; C. architecture | `run_recovery.py:329-345`, `:237`; `set_lifecycle.py:66-95`; `run_packet.py:229-240` | **E-04 SENDS THE EXECUTOR HUNTING FOR A SEAM THAT WAS ALREADY FINDABLE, AND MISSES THAT IT IS ENGINE-SIDE.** The invalidation seam is inside `plan_retry` itself (a `correction` record carrying `invalidates_seq`), with `set_lifecycle.make_invalidation_records` reusing the same idiom, so "locate it or stop and say so" is answered before execution. It also appends through `engine.store`, making it reachable only under some answers to OQ-03. Separately the correction PACKET has no shipped failed-predicate-only renderer | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 names the seam and forbids a second invalidation path, records that it is engine-side and therefore gated on OQ-03, and requires the packet-construction path be named by symbol rather than described abstractly. V-04 requires a grep showing exactly one producer of `invalidates_seq` per substrate. New F-13 |
| PR-006 | MEDIUM | UNDER-SCOPE | F. UX; A. correctness | `render_stream.py:2166-2171` (three statuses, `driver_error` key) versus `:2157-2165` and `:2172-2173`; `oc_runipd.py:317-334`; `runner_shutdown.py:64-83`, `:299-325` | **E-05's "RECORD IT WHERE A READ SURFACE CAN FIND IT" IS NOT SUFFICIENT, WHICH IS THE EXACT FAILURE ITS OWN F-11 DESCRIBES.** The diagnostics renderer keys off one specific field name for exactly three statuses; a reason written under any other key renders nowhere despite living in per-item state. And budget exhaustion cannot introduce a new status: the vocabulary is closed and `observe_ledger` declares a run incoherent on any value outside it, so an invented status would make every later shutdown observation report the run broken | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-05 now requires RENDERED evidence rather than a state dict, names the exact renderer branch and key, and requires the chosen status be a member of both closed sets with `observe_ledger` returning coherent. V-05 requires all of it pasted. F-11 rewritten from "no surface greps the event" to the sharper field-name form. New F-18 |
| PR-007 | MEDIUM | IN-SCOPE | E. testing; evidence accuracy | `runner_shared.py:2131-2152` (`refuse_frozen_flags_on_resume`); `tests/test_run_recovery_cli.py:133-143` | **TWO OF E-06's SIX BOUNDARY CASES ARE ALREADY GREEN, so presenting all six as proving the wiring would overstate the evidence.** The resume case is guaranteed by an outright REFUSAL of `--retry-budget` on resume, not by the loop reading a frozen value, and idempotency is already pinned by an existing test. Both are worth keeping as regression coverage, but a blanket "assert the cases fail before the change" is false for them | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 requires each case be labelled new-behavior proof or characterization, with its pre-change result measured at the executor's own named HEAD rather than at a stale sha. V-06 requires per-case pre-change results. New F-17 |
| PR-008 | MEDIUM | IN-SCOPE | G. executability; scope discipline | `Scope-Paths` versus the three OQ-03 shapes; `.aw/records/plans/pending/20260907-orchprobe-01-r2i1b1-...ipd.md:8-11` (`approved`, still pending, three-file overlap) | **`Scope-Paths` FITS ONLY ONE OF THE THREE POSSIBLE SHAPES, and the plan asserts "Over-scope: none" as though the declaration were settled.** Under shape (a) it needs the ledger-wiring paths; under shape (c) it needs `run_cli.py`/`ipd_set_plan.py`/`set_lifecycle.py` and drops a runner module. The runners announce declared paths before a run and the finalize gate reconciles actual against declared, so executing under the wrong declaration fails late. E-05 also cited `r2i1b1` as possibly-landed when it is `approved` and still pending with a three-file overlap | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Scope check now states plainly that the declaration is shape-dependent, forbids executing under shapes (a)/(c) without re-declaring first, and explains why `render_stream.py` is deliberately absent. E-05 records `r2i1b1`'s real disposition and treats the relationship as merge ordering. New F-19 |
| PR-009 | LOW | UNDER-SCOPE | Spec sync; A. correctness | spec `25kzda` `:960-990` (five retryable, ten never-retryable classes verbatim), `:905-908` (5.3 lists the frozen budget among LEDGER contents), `:899-901` ("the storage location is an implementation detail; the data contract is not") | **THE PLAN PARAPHRASES THE SPEC WHERE THE SPEC IS ENUMERATIVE, and does not notice that 5.3 assumes the very substrate PR-001 shows is absent.** Section 5.5 names its retryable and never-retryable classes exhaustively, which is a stronger starting point for E-01's allowlist than deriving one from the drivers' vocabulary alone. Section 5.3 lists "frozen retry budget, and remaining retries" among the ledger's required contents, so a shape-(b) implementation satisfies 5.5's semantics on a substrate 5.3 does not describe | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section now quotes both enumerations, states the 5.3 tension explicitly, and requires the executor to say whether shape (b) needs a spec amendment (declaring the spec path first) or is an acceptable implementation-detail difference under 5.3's own storage-location sentence. E-01 now derives its allowlist from 5.5's enumeration |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the substrate mismatch (PR-001) be resolved by the reviewer picking one of the three shapes, or escalated? | Escalate as blocking OQ-03 with three costed shapes and a recommendation | Picking shape (b) myself (ships the release-gated value fastest); picking shape (c) myself (smallest and most faithful to E-03); marking the plan REJECT - NEEDS REPLAN | Each shape is a scope/priority call, and shape (b) creates a second implementation of semantics other code will depend on, so it is irreversible in the sense Step 3.1 defines. Two sibling artifacts explicitly decline the same decision: `i1hlgx` ("whether drivers SHOULD write a ledger is genuinely open") and executed `7wei1o` (calls it "a genuine design question"). REPLAN rejected because E-01, E-02, E-06 and E-07 are sound under every shape, so bounded edits plus one answer repair it | no |
| D-2 | Is the plan's approach unsound enough to warrant `REJECT - NEEDS REPLAN` rather than `REVIEWED - OPEN QUESTIONS`? | REVIEWED - OPEN QUESTIONS | REJECT - NEEDS REPLAN | The goal, the allowlist design, the frozen-value discipline, the boundary matrix and the cross-host identity requirement all survive unchanged under all three shapes; only E-03/E-04 and the path declaration are shape-dependent. That is one answer plus a re-statement, which is bounded, not a replan | yes |
| D-3 | Should the plan keep `Blocks-Release: next` given it may not be executable as written? | Keep it | Clear it until OQ-03 is answered | The gate is INHERITED from backlog `trjfyy`, which carries `- Blocks-Release: next` and is `graduated` to this plan. Clearing it here would silently drop a release gate the item handed off, which is exactly what the close-legitimacy rule exists to prevent. The gate describes the WORK's importance, not the plan's current readiness | yes |
| D-4 | Should the reviewer fix the stated baseline's underlying cause (the `opencode-recovery/` tree tripping a parity test)? | No: record it, name the cause, and forbid touching it | Deleting or gitignoring the tree; adding the paths to the test's expected set | The tree is another party's gitignored session transcripts in a shared checkout, and the shared-checkout rule forbids reverting, cleaning up or committing work that is not mine. It is also outside this plan's `Scope-Paths` and outside a review's authority (reviews change plans, not code) | yes |
| D-5 | E-06's fixture rule cites an invented count ("23 tests"). Drop the citation or keep the rule? | Keep the rule, drop the number, cite the header lines that actually state the rule | Removing the fixture requirement entirely; leaving the number in place | The RULE is real and load-bearing (`tests/test_run_viewer.py:1-5` and `:22-27` both state it, and lane worktrees genuinely lack `.aw/records/runs/`). Only the count is unsupported: that file has 75 test functions and no occurrence of `23`. Keeping an unverifiable number next to a true rule invites an executor to trust the next number too | yes |

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
| PR-001 | BLOCKER | IN-SCOPE | C. Architecture (helpers need an unwired substrate) | plan OQ-03 (`- Status: resolved`, `- Finding: PR-001`) | Carried forward from round 1 and now CLOSED BY THE MAINTAINER. Round 1 measured that the plan as declared had NO executable form: `plan_retry` takes a `RunEngine` first, zero `ledger.jsonl` files exist across 143 run directories, neither driver references that machinery, and the two sides' status vocabularies are disjoint. Ruling of 2026-09-10: spend the budget in the DRIVERS' OWN `state.json`/`events.jsonl` substrate, reusing the helpers' SEMANTICS without calling the ledger-bound functions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Closed on the maintainer's decision. Accepted cost recorded: this is a SECOND implementation of retry semantics, so the executor MUST note at the implementation site that `run_recovery.py` remains the intended long-term home and that this was a deliberate decision. The semantics that must survive the substrate change are named, including evidence invalidation, which is the dangerous half to drop. This does NOT decide whether drivers should ever write a ledger. |
| PR-002 | HIGH | IN-SCOPE | F. Sequencing (half a correction loop) | plan OQ-01 (`- Status: resolved`, `- Finding: PR-002`) | Carried forward from round 1 and now CLOSED. Round 1 found this plan and `1bfppy` form two halves of one loop (a budget with no correction route is dead), and that the question's premise had expired since `wyw936` is now graduated and owned by a reviewed plan. Ruling of 2026-09-10: land `1bfppy` FIRST, then this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Closed on the maintainer's decision. Deliberately NO `- Item-Dependencies:` edge was added, and the contrast is recorded: for `xo3244` in the same round an edge WAS declared because the wrong order fails silently, whereas here the wrong order merely half-builds the loop, so an edge would block on preference. Shared-file overlap with `1bfppy` verified as merge ordering rather than a hazard. |
