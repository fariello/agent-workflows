# Review findings: plan 2o5wka

- Subject-Id: 2o5wka
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-301 (HIGH, fixed), PR-302 (MEDIUM, fixed), PR-303 (MEDIUM, fixed), PR-304 (MEDIUM, fixed), PR-305 (LOW, fixed), PR-306 (LOW, fixed)

## Round 1

Reviewed at HEAD `fd5fbe73` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported exit 0 with one advisory (`IPD-Z602`) BEFORE semantic review;
`--phase review-finalize --agent` reports the same after revision, and the advisory is assessed below
rather than dismissed.

THIS IS THE BEST-EVIDENCED PLAN I HAVE REVIEWED IN THIS SWEEP, AND EVERY SUBSTANTIVE CLAIM RE-VERIFIED.
I did not read its numbers; I re-ran its work. F-01 is exact: `evaluate_blocking_close`'s HANDOFF arm
returns `CloseVerdict(True, "ok", ..., "HANDOFF")` from inside `for _p, carrier_br in
find_from_backlog_artifacts(...)`, guarded by `if _carrier_is_executed(_p)`. F-02 is exact, including the
quoted comment naming `dh0uno`. The divergence reproduced verbatim on a scratch fixture
(`legitimate=True path=HANDOFF` against `close=False`, reason `IPD carrier(s) not executed:
.aw/records/plans/pending/20260101-s-01-dddddd-p.ipd.md`), and F-03's hand close reproduced END TO END:
`aw backlog set bbbbbb --status done` exited 0, printed `-> done`, and the item moved from `graduated/`
to `done/` with half its work unwritten. F-04's `or is_exec` fold is exact. F-05 is exact, docstring
enumeration included. F-09 verified (zero `orphaned-live-blocker` warnings live). I also re-prototyped
E-04's minimal edit and confirmed all four of its behavioral claims (mixed refuses, all-executed allows,
single-executed still allows, three-carrier-with-one-pending refuses), ran the FULL suite under it and got
exactly `1 failed, 3290 passed, 2 skipped` with the sole failure being the named test, and confirmed
F-08's grandfathering: all four already-`done` exposed items flip to `legitimate=False` while
`aw check release-gates` still reports `errors 0, warnings 0`. The exposed set was IDENTICAL to the
plan's: the same seven id6s, statuses and counts. The prototype was reverted; the tree is clean.

So the fix direction, the convergence target, the blast radius and the grandfathering answer are all
correct and independently reproduced. What review found is a documentation gap the plan's own reasoning
should have caught, a co-editor it did not know about, and a lint violation it was carrying.

THE ONE WORTH THE MOST ATTENTION (PR-301). E-06 updates two prose sites and argues carefully that
`engine.py` is out of scope, which I verified (`grep -c Close-legitimacy agent_workflows/engine.py` is 0,
so the `AGENTS.md` paragraph is genuinely repo-local). But the plan then asserts that the managed hook
template "does mention 'HANDOFF via a From-Backlog plan'" and "stays true". That is not its text: both
occurrences read "HANDOFF via an EXECUTED From-Backlog plan or implemented spec", and a THIRD site the
plan never mentions, `hooks/backlog_blocking_close_gate.py`'s module docstring, reads "HANDOFF (a
`From-Backlog` blocking plan present in the staged tree with the same `Blocks-Release`)". Both become
imprecise under the fix. This matters more than a wording nit because the `engine.py` template is
INSTALLED INTO EVERY MANAGED TARGET, so it is the contract a managed repo's operator reads. I kept them
out of scope for the plan's own good reason (an install-surface edit has a categorically different blast
radius, and folding it in would undo the reasoning E-06 used to exclude `engine.py`), but a deferral with
no carrier is exactly the obligation loss this repository's carrier rule exists to stop. So I added OQ-03
and FILED the carrier (`d1ldvk`), rather than leaving a promise.

THE LINT VIOLATION IT WAS CARRYING (PR-303). `check.ipd-uncarried-obligation` reported EIGHT obligations
with no durable carrier: all six Deferred rows plus both open questions lacked any `Carrier:` or
`Carrier-Declined:` line. That is not cosmetic. The rule's own message states the consequence precisely:
once the plan reaches `executed` it classes `done` in `aw attention` and every one of those obligations
vanishes with no record. I wrote a SPECIFIC disposition for each rather than a blanket, and two of them
turned out to need real content: the plan-scope row cites `rwhbci` as its owner, and `rwhbci` is now
`- Status: done` with `2a6phj` executed, so that question is currently UNOWNED and the row now says so
and requires the executor to name it; and the `- Blocks-Release: -` row cites `ghna7l` as `reviewed` when
it is `approved`.

THE CO-EDITOR (PR-302). `47ttnv` (`reviewed`, `go-pending-approval`) declares `AGENTS.md` and its E-05
edits the SAME close-legitimacy paragraph as this plan's E-06a. I checked the split at sentence
granularity and they do not collide: `47ttnv` rewrites only the ENFORCEMENT claim (that one shared
predicate "backs the setter", singular, which read as true while the positional spelling bypassed it) and
its instruction explicitly forbids restating the three fixes, while this plan owns fix (1)'s carrier
count. Both independently verified the managed-block boundary. Lane isolation handles the mechanics; what
needed recording is the SEMANTIC split, because whichever lands second will find the paragraph already
changed, and an executor not told to expect that may revert it or re-litigate the boundary check.

THE COUNTS (PR-304). The plan is admirably careful to call its corpus integers non-durable, and review
proved it right: 706/374/351/36/18 at authoring became 746/386/414/40/21 one day later, and the suite
total moved 3245 to 3290. But two instructions still read as literal comparisons (E-07's "the prototype
produced exactly `1 failed, 3245 passed`" and the Required-tests reconciliation target). Both now state
the SHAPE as the bar with a lane-captured baseline, and carry both measurements so a third figure at
execution reads as expected drift rather than regression.

THE DENSITY ADVISORY, ASSESSED NOT DISMISSED (PR-306). `IPD-Z602` fires on E-03 ("action text may bundle
multiple concerns"). The rubric requires me to treat a sizing signal as a finding to investigate by
decomposition, so I read the target test file. JUDGEMENT: keep E-03 whole. Its five numbered parts are one
concern (the test-level contract for the new rule) in one file, sharing two fixture helpers and one
scratch-repo harness, so each part is a handful of lines differing only in carrier bucket and count.
Splitting would make V-03 unsatisfiable, since the before-failing proof it demands is a single run over a
single file. The genuinely separable piece, the `release_gate_warnings` fixture, is already its own item
(E-05) in its own file. Recorded on the item so a later reader sees the judgement rather than re-deriving
it.

WHAT I DELIBERATELY DID NOT FLAG. The plan reverses a shipped test on purpose, which is normally alarming.
Here it is correct and impeccably handled: it names the reversal three times, identifies the plan that
authored the original assertion and under which OQ, requires the new docstring to record the reversal so a
future reader does not "restore" the hole as a regression fix, and sequences E-03 before E-04 so the
before-failing proof exists. I also left OQ-01 resolved: its grandfathering answer is correct and I
reproduced the measurement it rests on. And I left the eight-item structure alone; each item has one
deliverable and a verifiable outcome, and E-01/E-02's measure-first items are load-bearing for a plan
whose whole subject is two predicates disagreeing.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | UNDER-SCOPE | G (documentation sync) | plan E-06 ("The managed hook TEMPLATE in `engine.py` does mention 'HANDOFF via a From-Backlog plan'"); `engine.py` actually reads "HANDOFF via an EXECUTED From-Backlog plan or implemented spec" at both occurrences; `hooks/backlog_blocking_close_gate.py` docstring reads "HANDOFF (a `From-Backlog` blocking plan present in the staged tree with the same `Blocks-Release`)" | The plan misquotes the template it clears as "stays true", and misses a third prose site entirely. Both become imprecise under the fix, and the `engine.py` one is INSTALLED INTO EVERY MANAGED TARGET, so it is the contract a managed repo's operator reads | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both sites quoted accurately in E-06 and kept OUT of scope on the plan's own install-surface reasoning; added OQ-03 and FILED carrier `d1ldvk` rather than promising one; V-06 now requires both quoted in the report |
| PR-302 | MEDIUM | IN-SCOPE | C (operability); concurrency | `47ttnv` `- Scope-Paths:` includes `AGENTS.md`; its E-05 edits the close-legitimacy paragraph and forbids restating the three fixes; it is `- Status: reviewed`, `- Readiness: go-pending-approval` | A reviewed plan co-edits the same paragraph and the plan does not know it. The split is non-colliding at sentence granularity, but an unwarned executor may revert the co-edit or re-litigate the boundary check | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12 with the measured sentence split; E-06 now names the co-editor and instructs leaving its edit alone; V-06 requires stating whether it landed |
| PR-303 | MEDIUM | IN-SCOPE | G (records) | `check_engine.evaluate_durable_carrier` reports "8 obligation(s) name no durable carrier": all six Deferred rows plus OQ-02 and OQ-03 | Every deferred obligation would vanish from `aw attention` when the plan reaches `executed`, which is precisely what the rule exists to prevent. Two rows also carried stale owners: `rwhbci` is `done` and `2a6phj` executed, leaving plan-scope coverage UNOWNED; `ghna7l` is `approved`, not `reviewed` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A specific `Carrier-Declined:` written per row (not a blanket), `Carrier: d1ldvk` on OQ-03, a triggered decline on OQ-02; the stale owners corrected and the now-unowned plan-scope gap flagged for the executor's report. `evaluate_durable_carrier` now reports CLEAN |
| PR-304 | MEDIUM | IN-SCOPE | E (testing); live-artifact convention | plan E-02 (706/374/351/36/18) vs review (746/386/414/40/21); plan E-07 ("exactly `1 failed, 3245 passed, 2 skipped`") vs review's re-prototype (`1 failed, 3290 passed, 2 skipped`) | The plan correctly warns its corpus integers will drift, but two instructions still read as literal comparisons against authored totals | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both measurements recorded side by side; E-07, Required tests and V-07 now state the SHAPE as the bar against a lane-captured baseline, noting the exposed SET was identical at review while the totals moved |
| PR-305 | LOW | IN-SCOPE | G (execution contract) | plan gate ("move this file to `.aw/records/plans/executed/`"); `ipd_lifecycle` `AW-LIFECYCLE-ROLE-001`; `find_from_backlog_artifacts(repo, 'lsbd32')` returns exactly one carrier, this plan | The gate instructed a hand move to `executed/`, and said nothing about the fact that `lsbd32`'s own close is now governed by the rule this plan ships | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Tooled `aw ipd finalize` with runner ownership and the `AW-LIFECYCLE-ROLE-001` path; added the measured single-carrier finding for `lsbd32` with the instruction to re-check for siblings and to report a refusal rather than work around it |
| PR-306 | LOW | IN-SCOPE | G (right-sizing) | `aw ipd lint --long`: "IPD-Z602 (line 51): E-03: action text may bundle multiple concerns"; `tests/test_backlog_handoff_close.py` helpers `_write_backlog_item`/`_write_plan` shared by every case | A sizing signal was left unaddressed; the rubric requires investigating by decomposition rather than dismissing | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Assessed and KEPT WHOLE, with the judgement recorded on E-03: one concern, one file, shared fixtures, and splitting would make V-03's single before-failing proof unsatisfiable; the separable piece is already E-05 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the two remaining "an EXECUTED plan" prose sites be folded into E-06's scope? | No: keep out of scope, add OQ-03, and FILE a carrier (`d1ldvk`) | Fold both into E-06; leave them undocumented as the plan did | Both become IMPRECISE rather than false (each names which arm exists and what carrier shape it accepts, not how many must have executed), and the `engine.py` one is installed into every managed target, so editing it is an install-surface change with a different blast radius from a repo-local paragraph. That is the same reasoning E-06 used to exclude `engine.py`, so folding it back in on a wording nit would undo it. Leaving them undocumented was not an option: a managed repo's operator reads the template as the contract | yes |
| D-2 | Was filing backlog `d1ldvk` from a review legitimate, and why not defer it to the plan's E-08? | Yes, filed at review | Promise it in E-08; leave the deferral carrier-less as authored | A backlog item is a planning document, so filing one is within this workflow's mandate. Deferring it to E-08 fails twice: the obligation would not exist if the plan never executes, and `check.ipd-uncarried-obligation` REFUSES a `Carrier:` value that is not a resolvable bare id6, so a promised carrier cannot be cited at all. The repository's own precedent is `sv9ce4`, filed at authoring time for exactly this reason; maintainer told 2026-09-30 in this review's final report, which names the filed carrier `d1ldvk`, its id6, its `open` status and the two prose sites it owns, so the decision is surfaced rather than merely logged | no |
| D-3 | Should E-03 be split, given `IPD-Z602` fires on it? | No: keep whole, record the judgement | Split into five test items; split into rewrite-versus-add | Read the target file: the five parts share `_write_backlog_item`/`_write_plan` and one scratch-repo harness, differing only in carrier bucket and count, so they are one concern executable in one pass. Splitting would make V-03 unsatisfiable, since its before-failing proof is one run over one file. The separable piece (the `release_gate_warnings` fixture) is already E-05 | yes |
| D-4 | What should the suite and corpus acceptance bars be, given both drifted between authoring and review? | The SHAPE, measured against a baseline captured in the executing lane | Update the numbers to review's figures; drop the comparisons | Updating just moves the staleness (more work lands before execution), and dropping loses the one-failure signal that bounds this change. Recording BOTH measurements and stating the shape is what makes a third figure read as expected drift. Note the exposed SET was identical at review while every total moved, which is exactly the plan's own point about which claim is durable | yes |
| D-5 | The plan-scope-coverage deferral cites `rwhbci`, which is now `done`. File a carrier for it? | No: record that it is unowned and require the executor to name it in the report | File a new backlog item now; leave the stale citation | Filing an item for an adjacent design question this review has not analyzed would be filing a stub, and the question (does a carrier's declared SCOPE cover the whole item) is a different axis from carrier COUNT and needs its own analysis. What is owed is visibility, which the row now carries with the measurement that `rwhbci` is closed and `2a6phj` executed, enough for a maintainer to file it without re-deriving anything | yes |
