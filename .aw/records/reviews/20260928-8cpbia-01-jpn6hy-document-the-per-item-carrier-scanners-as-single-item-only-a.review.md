# Review findings: plan jpn6hy

- Subject-Id: jpn6hy
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `cd967ae7` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize --agent`
conforms after revision with zero findings and zero advisories. No pre-review snapshot was owed: the
plan was committed and unmodified with `git status --porcelain` empty at review start. The plan carries
`- Kind: child`, so the `IPD-S407` orchestrator row check does not apply. Every measurement was taken
by importing the package in-process and by one synthetic two-item repository under the gitignored
`.aw/workflow-artifacts/`, which was removed afterwards.

THIS IS AN UNUSUALLY WELL-MEASURED PLAN AND MOST OF THE REVIEW WAS RE-DRIVING IT. Eight of its nine
findings reproduce, several exactly. F-01: all three functions walk their trees per call with no
memoization and one-line docstrings that mention only the return value. F-04: an independent AST sweep
finds exactly four call sites (two internal to `find_from_backlog_artifacts`, plus
`evaluate_blocking_close`'s HANDOFF branch and `runner_shared.evaluate_backlog_close`'s comprehension)
and the loop-bound/argument intersection is EMPTY at all four, so the `chore` classification is right.
F-06: the eight-fixture behavior reproduces case for case, flagging the direct loop variable, the dict
comprehension, the `it.id` attribute form, the nested inner variable and the `item_id6=i` keyword form,
passing the bare call and the iter-position form, and missing `tmp = i`. F-07 is the sharpest of them:
keying on "is there an enclosing loop" really does flag the correct `runner_shared` call, and keying on
whether the ID6 ARGUMENT is loop-derived really does exonerate it, which I confirmed by building both
analyzers. F-08 and F-09 verify by reading. The plan's central design decision is sound and its
rejection of the backlog item's fix (b) is correct.

I RE-DROVE F-05 RATHER THAN TRUSTING IT, BECAUSE IT IS THE LOAD-BEARING CLAIM, and it reproduces
exactly, including the mechanism. On a fresh synthetic two-item repository, performing the runner's real
sequence through the real `evaluate_backlog_close` (move this item's plan `pending/` to `executed/`,
then evaluate that item's close, once per item, one process): the live scanner closes both items, and a
process-lifetime cached index closes the first and REFUSES the second with `close=False rule=None
reason='IPD carrier(s) not executed: .aw/records/plans/pending/20260928-bbb222-01-bbb222-x.ipd.md'`,
citing a path the plan had already left. `plan_bucket` on that vanished path returns `pending` rather
than raising, so the refusal is silent. The rejection of fix (b) is evidence, not argument.

THE FINDINGS ARE THEREFORE ABOUT TWO THINGS THE PLAN DID NOT MEASURE, plus figures that moved. FIRST
AND MOST SERIOUS: the guard's `agent_workflows/` scope is LOAD-BEARING and the plan never says so.
Pointing the same analyzer at `tests/` flags TWO calls in `tests/test_check_engine_release_gate.py`,
where a sentinel-handling test deliberately loops over `-`, `none`, `unresolved` and asks the scanner
about each. Those calls are correct (three cheap calls on a synthetic two-file repo). So the single most
obvious "improvement" to this guard, widening its root, turns the suite RED with only bad remedies
available: an allowlist, or degrading a valid test to satisfy a guard about production call shape. A
plan whose entire purpose is to stop a shape being re-learned should record the boundary that makes its
own guard correct.

SECOND: the suite baseline is INVERTED, which is the third sibling plan in this sweep with the same
defect. F-03 told the executor to expect `1 failed, 3038 passed`, to compare against it, and that a
fully green line "needs explaining rather than celebrating". Commit `f1b5b9ff` fixed that failure using
exactly the remedy carrier `03aicr` proposed; the suite is green at `3081 passed, 2 skipped`. As
authored the plan teaches an executor to accept a red suite and distrust a clean one. It also leaves
`03aicr` stale while still `open` and still carrying `- Blocks-Release: next`, so a release is gated on
completed work. The review does NOT close that item and requires E-03 to report it.

THIRD, AND SOFTER: F-02's figures are less stable than the plan allows. It correctly warns that the
ratio is not a constant across item counts, but then instructs E-02 to write 598x into a docstring. A
review re-run on a barely-changed corpus (883 plans against 878) measured the shared walk at 1.023 s
rather than 259 ms and the extrapolated ratio at roughly 449x, because page-cache state dominates a tree
walk. The durable claim is the SHAPE, and a docstring pinning a ratio would itself become the stale
prose this plan exists to prevent. I also found the mapping-equality check needs care: a naive sample of
the first 60 items finds ZERO with carriers, so equality must be checked on carried items (278 exist; 40
checked identical).

WHAT THIS REVIEW DID NOT CHANGE. The guard-not-optimization framing, the iter-position discriminator,
the decision to put the guard in the test suite rather than in `aw check` (OQ-02, whose division of
labour argument is correct: no shipped check rule parses the package's own source), the three
Carrier-Declined dispositions, the docstring-only risk posture, and the no-spec-amendment argument all
stand. I verified V-02's docstring-only proof is actually feasible on a 7000-line module by performing
the strip-and-`ast.dump` comparison on a simulated E-02 edit; the dumps are identical, so that evidence
requirement is sound as written rather than aspirational.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-A01 | HIGH | UNDER-SCOPE | E. Testing / G. Plan executability | Review run of the analyzer over `tests/test_check_engine_release_gate.py` printing `INTERSECT=['sentinel']` at two call sites; read of those sites showing a deliberate loop over the three sentinel values against a temporary repo | **THE GUARD'S `agent_workflows/`-ONLY SCOPE IS LOAD-BEARING AND THE PLAN NEVER SAYS WHY.** The same analyzer pointed at `tests/` flags two LEGITIMATE calls, so the most obvious future "improvement" (widen the root) turns the suite red, and its cheap remedies are an allowlist or degrading a valid test. For a plan whose whole purpose is stopping a shape from being re-learned, leaving its own guard's boundary unexplained invites exactly that. | C:Low; U:Low; S:Low; F:Low; Overall:Low (one measured sentence in the module docstring) | FIXED | E-01 now states the `agent_workflows/`-only scope as a REQUIREMENT with the measurement as its reason, and requires that reason recorded in the module docstring so a later contributor learns it before the suite goes red. New F-10. |
| PR-A02 | HIGH | IN-SCOPE | D. Anti-regression / E. Testing | Bare `python3 -m pytest` at review printing `3081 passed, 2 skipped, 3 warnings in 48.50s`; targeted run printing `8 passed in 0.18s`; `03aicr` still `- Status: open` with `- Blocks-Release: next` | **THE BASELINE IS INVERTED AND THE CARRIER IS STALE.** F-03 instructs the executor to expect one failing test, to compare against `1 failed, 3038 passed`, and that a green line "needs explaining rather than celebrating". Commit `f1b5b9ff` fixed it with the remedy `03aicr` itself proposed, and the suite is green. So the plan teaches an executor to accept red and distrust clean. Separately `03aicr` still gates a release for completed work. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-03 rewritten with both measurements and the repairing commit; the bar restated as ZERO failures against a baseline re-derived at lane start; E-03, V-03, the Deferred row and the gate paragraph corrected. E-03 now requires `03aicr`'s staleness REPORTED and explicitly NOT closed (another party's item; a gated close has its own predicate). |
| PR-A03 | MEDIUM | IN-SCOPE | D. Anti-regression (live measurements) | Review re-run printing `corpus: 883 plans, 38 specs, 673 items`, `ONE shared index walk: 1.023s`, `25 per-item calls: 17.052s -> extrapolated 673 calls: 459.0s`, `extrapolated ratio: 449x` against the authored 598x with a 259 ms shared walk | **THE PLAN WARNS THAT THE RATIO IS NOT A CONSTANT AND THEN INSTRUCTS E-02 TO WRITE ONE INTO A DOCSTRING.** The shared-walk term moved by 4x on a corpus that grew by 5 plans, because page-cache state dominates a tree walk, so 598x is a snapshot. A docstring pinning it becomes the stale prose this plan exists to prevent, in the very file it is documenting. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 carries the review re-measurement and states that BOTH sets are snapshots; E-02 now requires the measurement dated and explicitly flagged as not a constant, with the durable claim being the SHAPE (one walk per call, hence O(items x corpus)); V-02 requires that confirmed rather than accepting a bare ratio. |
| PR-A04 | LOW | IN-SCOPE | E. Testing (evidence method) | Review probe: `checked 60 items: identical=60 mismatched=0 (with carriers: 0)` against `items WITH carriers in the index: 278` and `checked 40 CARRIED items: identical=40 mismatched=0` | F-02's mapping-equality claim is TRUE but its method needs care that the plan does not record: the first 60 backlog items have ZERO carriers, so a naive sample asserts equality of empty sets and proves nothing. Equality must be checked on items that actually have carriers. The plan's own figure (273 of 273) shows the author did this; the plan does not say so, and an executor re-driving it could easily not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02's evidence now records the review re-confirmation on CARRIED items with the count (278 carried; 40 checked identical) and states explicitly why a naive first-N sample proves nothing. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The guard flags two legitimate calls if pointed at `tests/`. Narrow the guard's scope, allowlist those calls, or widen and fix the tests? | KEEP the `agent_workflows/`-only scope and RECORD the reason in the module docstring. | (a) Widen to `tests/` with an allowlist - REJECTED: an allowlist is a second list to maintain and the first entry would be a test that is entirely correct, which teaches a reader the guard's judgement is unreliable. (b) Widen and rewrite the sentinel test to avoid the loop - REJECTED as backwards: the test is right (three cheap calls on a synthetic two-file repo asserting sentinel absence), and degrading real coverage to satisfy a guard about PRODUCTION call shape inverts the purpose. (c) Narrow silently, as the plan already did - REJECTED as the status quo this finding is about: the boundary is load-bearing, so leaving it unexplained is what invites the breaking "improvement". | Review run flagging `INTERSECT=['sentinel']` at two `tests/test_check_engine_release_gate.py` sites; read of those sites; the plan's own thesis that an unexplained contract gets re-learned | yes |
| D-2 | The authored suite baseline names a failure that is fixed, and its carrier is still release-gated. Update the number, close the carrier, or report it? | RESTATE THE BAR as zero failures re-derived at lane start, and REPORT the stale carrier without closing it. | (a) Close `03aicr` here - REJECTED: another party's item, closing a `Blocks-Release` item runs a gated predicate requiring handoff, evidence or de-gating, and clearing a release gate should be a deliberate human act rather than a side effect of a `chore`. (b) Substitute `3081 passed` as the new bar - REJECTED: the count moved 3069 -> 3075 -> 3081 across three reviews in this same sweep, so a fresh fixed figure expires identically; the live-artifact convention makes a drifting count context, never the bar. (c) Say nothing since green is good news - REJECTED: a still-open release-gated item for completed work is a real defect in the release view, and silence is how it persists. | bare suite green at review; `f1b5b9ff`; `03aicr`'s own suggested remedy matching what landed; its front matter still `open` + `Blocks-Release: next`; the AGENTS.md close-legitimacy rule | yes |
| D-3 | F-02's ratio is unstable across runs. Re-measure and substitute, drop the number, or change what the docstring asserts? | ASSERT THE SHAPE in the docstring, and keep every measurement dated and labelled a snapshot. | (a) Substitute the review figures (449x, 1.023 s) - REJECTED: no more canonical than the authored ones, since the shared-walk term is dominated by page-cache state; substituting only moves the expiry date. (b) Drop the numbers entirely - REJECTED: the measurement is what makes the docstring persuasive rather than a scold, and F-02 is the argument for the whole plan. | the two review timings against authoring's; the three-way disagreement between the item's 54x, the plan's 598x and review's 449x; the plan's own warning that the ratio scales | yes |

### Deferred and open

None. Every finding is FIXED. No finding was left OPEN or DEFERRED, so no escalation to a
`- Blocking: yes` open question is owed under the repository's `HIGH` gate threshold. The plan's two
open questions were already `resolved` and remain so: OQ-01's rejection of the backlog item's fix (b)
was INDEPENDENTLY RE-DRIVEN at review (both verdict pairs reproduced, including the silent
`plan_bucket` mechanism, F-11) and stands exactly as authored; OQ-02's choice of a test over an
`aw check` rule was re-checked against the repository's actual division of labour (check rules police
`.aw/` records, no shipped rule parses the package's own source, and `tests/test_host_capability_wiring.py`
is the standing precedent for a source-shape assertion) and stands. The three Carrier-Declined
dispositions are correct: each records a rejected design alternative rather than outstanding work. The
one `Carrier:` row cites `03aicr`, which resolves and is live, though now stale for the reason PR-A02
records. No decision above carries `Reversible: no`.

THE PLAN CORRECTLY CLAIMS NO RELEASE GATE. Backlog `8cpbia` carries no `- Blocks-Release:`, its
`- Work-Kind:` is `chore`, and the repository's auto-gating set is `bug` alone, so none is owed. F-04's
perceptibility reasoning supports the `chore` classification and was verified: no shipped call site is
quadratic, and `aw check release-gates` completes in 2.9 s at review, so nobody waits on the cost this
plan documents.

FINAL GATES: `aw ipd lint --phase author --agent` exit 0 `findings: 0` before revision;
`--phase review-finalize --agent` exit 0 `findings: 0` after, with zero advisories; `aw check` unchanged
at its pre-existing findings with none on this plan; bare `python3 -m pytest` -> `3081 passed, 2
skipped, 3 warnings in 48.50s`; `aw check release-gates` 2.9 s; `aw sanitize --agent` clean; the
synthetic probe repository deleted and `git status --porcelain` showing exactly the plan (modified) and
this record (new).
