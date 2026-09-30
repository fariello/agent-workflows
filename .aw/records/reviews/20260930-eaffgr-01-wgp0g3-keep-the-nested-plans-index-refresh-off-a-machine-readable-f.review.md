# Review findings: plan wgp0g3

- Subject-Id: wgp0g3
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-901 (HIGH, fixed), PR-902 (MEDIUM, fixed), PR-903 (MEDIUM, fixed), PR-904 (LOW, fixed), PR-905 (LOW, fixed), PR-906 (MEDIUM, fixed)

## Round 1

Reviewed at HEAD `7ecee68b` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `conforming` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply.

THE DIAGNOSIS AND THE FIX ARE BOTH RIGHT, AND I RE-DERIVED ALL THIRTEEN FINDINGS RATHER THAN READING THEM.
F-01 reproduces exactly: on the success path `aw ipd finalize --apply --json` exits 0 with 71 stdout lines
whose first is `'plans index --check: clean'`, and `json.loads(stdout)` raises `JSONDecodeError: Expecting
value: line 1 column 1 (char 0)`; `--agent` is affected identically at 2 lines. F-03's mechanical cause
reproduces: `quiet` is read at exactly two places in `plans_index.run_index`, both AFTER the check
branch's return, so neither of that branch's two printing arms consults it. F-04 reproduces (the drift arm
pollutes too). F-05 reproduces (the regeneration call printed the empty string on every tree). F-06
reproduces as a clean 2x3: refusal and `begin` parse under both flags, only the success path breaks. F-07
reproduces (a tampered manifest is cured by the refresh's own regeneration, so `name-metadata-mismatch` is
the right lever). F-08 reproduces verbatim, including that the serialized payload contains
`name-metadata-mismatch` NOWHERE. F-10 and F-11 reproduce. And F-09's central claim, the one the whole plan
rests on, reproduces on every tree I tried: `check_drift` + `drift_exit_code` returns the SAME verdict as
`run_index(check=True)` and prints the empty string, with rendered drift text byte-identical to what the
old call printed.

SO THE APPROACH IS SOUND AND MY FINDINGS ARE PRECISION DEFECTS IN THE TESTS AND THE MESSAGE, not in the
design. I say that explicitly because the count of findings could otherwise read as doubt about the fix.

THE ONE THAT MATTERS MOST IS A VACUOUS ASSERTION. E-03(d) told the executor to assert that the payload
"names BOTH the offending plan path and the literal rule". Measured at HEAD on the non-convergence tree,
`'zzzz99' in json.dumps(payload)` is already **True**, because the `IPD-FINALIZE` diagnostic's `location`
is the plan file and that filename carries the mismatching id6. So half of the required assertion passes
before the fix and pins nothing; only `name-metadata-mismatch` (measured **False** at HEAD) discriminates.
In a plan whose own V-03(a) correctly insists that a test which does not fail at HEAD has pinned nothing,
shipping a required assertion that half-passes at HEAD is the defect worth catching.

TWO MEASUREMENTS THE PLAN DID NOT MAKE, both about severity. First, E-02 would have rendered EVERY finding
`check_drift` returned into a message explaining a REFUSAL, but `drift_exit_code` treats `info` as
advisory, so a tree can carry advisory findings and still converge: measured, an ungenerated-manifest tree
yields two `check.stale-index-missing` findings at severity `'info'` and rc **0**, while the old
`run_index(check=True)` returns 0 there and prints both lines anyway, so the print and the verdict already
disagree at that point. On a tree with both an advisory finding and a genuine mismatch, the unfiltered
render would name paths that are not the reason. E-02 now filters on `drift_exit_code`'s own predicate, and
the decision is recorded as OQ-03. Second, V-01 asked for three trees and none of them is the `info` case,
which is exactly the class the cited `yvvf98` E-02 bug lived in; a fourth tree is now required, and I
verified it agrees (both surfaces return 0), so it is a confirmation to reproduce rather than a suspected
divergence.

TWO SMALLER TEST TRAPS. The drift `location` is relative to the plans dir and its FIRST SEGMENT IS THE
DISPOSITION, which changes mid-transaction: the same finding reads `pending/...` before finalize and
`executed/...` in the message the post-reconciliation refresh actually produces, so a test pinning a
`pending/` prefix would fail for a reason unrelated to the fix. And the `--agent` half of E-03(a) needed
strengthening, because a per-line JSONL scan of the polluted `--agent` stdout ALREADY recovers exactly one
payload-shaped record at HEAD; "every line parses" is the assertion that fails before the fix, while
"a payload is recoverable" passes. That last measurement also bounds the plan's severity honestly: the
contract violation is real on both flags, but a conforming `--agent` consumer survives today and a `--json`
consumer does not.

THE PLAN ALSO TRIPPED THE REPOSITORY'S OWN CHECKER, TWICE, both pre-existing. `aw check` reported
`check.lifecycle-transition-invalid` on it, because the authored history listed its `draft` record BELOW
its `to-review` record and the section is newest-first, so `check_lifecycle_transitions` read a backwards
`to-review` -> `draft` transition. It also reported `check.ipd-uncarried-obligation`, because none of the
four `## Deferred` rows carried a carrier line. I fixed both: the redundant `draft` record is folded into
the `to-review` one (the plan was authored in a single turn, so that is the accurate history), the
`plans_refs` row now carries backlog `eeiytw` which I filed from F-12's own measurement, and the other
three rows carry `Carrier-Declined:` reasons because each is a rejected alternative, a deliberately-kept
complementary parser, or a clean audit result. This mattered enough to fix rather than note: the plan
carries `Blocks-Release: next`, and a release-gating plan that trips the consistency checker it ships
cannot be approved on the promise that someone will notice later.

ONE FIXTURE COST RECORDED FOR THE EXECUTOR, because it cost me three iterations: a probe plan needs an
`- Approval:` bullet or `aw ipd begin` refuses with `IPD-M104`; its `## Deferred` rows each need a carrier
line or finalize refuses with `check.ipd-uncarried-obligation`; and `aw ipd begin` takes no `--apply`. The
plan's own F-13 note about dropping `AW_EXECUTION_ROLE` is correct and I hit that too.

WHAT I CHECKED AND LEFT ALONE. The conventions section is accurate throughout, including the
`drift_exit_code` severity contract, `check_drift` being an established pure seam with a second direct
consumer in `check_engine`, and the load-bearing name and signature of
`_refresh_plans_index_fail_loud` (tests patch it, count its calls and invoke it directly, which V-01(a)
correctly guards). `LC.PHASE_COMMITTED_INCOMPLETE` exists and a genuine non-convergence really does reach
it (journal `phase='committed-incomplete'`, commit not rolled back), so E-03(c) is buildable as written.
OQ-01 and OQ-02 are both sound and correctly non-blocking, and OQ-02 is the right call to surface for a
maintainer rather than decide silently. The spec-sync section's reasoning is correct: this plan makes code
obey three already-written contracts and amends none.

Nothing in `agent_workflows/` or `tests/` was modified. All probe work lived in gitignored scratch under
`.aw/state/`; `git diff --stat agent_workflows/ tests/` is empty.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | E. Testing (a required assertion that half-passes before the fix) | On the `name-metadata-mismatch` tree under `--json` at HEAD, balanced-brace recovery yields a payload with `'zzzz99' in json.dumps(payload) == True` and `'name-metadata-mismatch' in json.dumps(payload) == False`. The cause is mechanical: the `IPD-FINALIZE` diagnostic's `location` is the plan file whose filename carries the id6 | **E-03(d) requires asserting the payload names the offending plan path, and that already passes at HEAD**, so half the assertion pins nothing. Only the rule name discriminates. In a plan whose V-03(a) rightly insists a test that does not fail at HEAD has pinned nothing, a half-vacuous required assertion is the defect that matters | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03(d) now keys on `name-metadata-mismatch`, states that the path half is vacuous against the serialized payload, and requires any path assertion to target the `summary` or diagnostic `detail` specifically. V-02(b) restated the same way and forbids accepting a path-only match. F-14 records the measurement |
| PR-902 | MEDIUM | IN-SCOPE | A. Correctness (a message that could name findings that are not the reason) | An ungenerated-manifest tree yields two `check.stale-index-missing` findings at severity `'info'` with `drift_exit_code` returning **0**; the old `run_index(check=True)` returns 0 there while printing both lines. The mismatch finding carries severity `''` (legacy 3-field `Drift`) and correctly fails | **E-02 would render every `check_drift` finding into a message explaining a REFUSAL, but `info` findings do not cause the refusal**, so on a tree carrying both an advisory finding and a genuine failure the message would name paths that are not the cause, and the message and the verdict would disagree | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 now filters to `severity != "info"` before rendering, naming `drift_exit_code`'s own predicate so message and verdict cannot diverge. New OQ-03 records the decision with three rejected alternatives. V-02(e) requires the mixed-tree evidence. F-16 records the measurement |
| PR-903 | MEDIUM | IN-SCOPE | D. Anti-regression (the one interesting equivalence case is unmeasured) | `yvvf98` E-02 is cited by the plan itself as the bug where a hardcoded `return 1` made two surfaces disagree on an `info`-severity tree. V-01's three trees (clean, mismatch, tampered) contain no `info` finding. Review measured the fourth tree and both surfaces return 0 | **V-01 demands verdict-equivalence on three trees, none of which exercises the `info` severity path** that the plan's own conventions section identifies as the historical divergence class. The equivalence claim would be evidenced everywhere except where it was previously broken | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01(b) now requires FOUR trees including a never-generated-manifest tree, states why it is the only one exercising `info`, and records that review verified it agrees so the executor knows it is a confirmation not a suspicion. V-01(c) extends the silence proof to all four and pastes the HEAD baseline for contrast |
| PR-904 | LOW | IN-SCOPE | E. Testing (two assertions that would pass or fail for the wrong reason) | Drift locations measured on one tree: `['pending/...zzzz99...', 'INDEX.json', 'INDEX.md']` before finalize, `executed/...zzzz99...` in the line the refresh emits, `['executed/...']` after. Separately, a per-line JSONL scan of polluted `--agent` stdout recovers exactly one `schema == "aw.agent/v1"` record at HEAD (`--json` recovers zero) | **Two test traps.** The drift location's first segment is the DISPOSITION and changes mid-transaction, so a literal `pending/` prefix would fail unrelatedly; and E-03(a)'s `--agent` assertion, if written as "a payload is recoverable", passes at HEAD and pins nothing | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03(d) instructs asserting on the filename or id6 rather than a disposition prefix (F-15). E-03(a) now mandates "every line parses" for `--agent` with the measurement explaining why payload-presence is insufficient (F-17). F-17 also records the honest severity bound: the violation is real on both flags, the practical breakage is `--json`-specific |
| PR-905 | LOW | UNDER-SCOPE | G. Plan executability (an incomplete gate and three undocumented fixture prerequisites) | The gate carried the commit/never-push rule and the bare-run instruction but no scope fence, no open-questions statement, and a transition paragraph with no conditional-ownership distinction. Review hit three fixture refusals in sequence: `IPD-M104` (missing `- Approval:`), `check.ipd-uncarried-obligation` (Deferred row with no carrier), and `unrecognized arguments: --apply` on `aw ipd begin` | **The gate omits a scope-fence declaration, the open-questions statement, and the conditional runner/executor ownership of the transition**, and no V-item warns of the three fixture prerequisites an end-to-end probe must satisfy | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate gains the paste-the-actual-output honesty MUST, a declaration-style scope fence naming two genuinely-unsafe stop conditions (a concurrent `ipd_lifecycle.py` edit, and finding documentation that promises the line F-10 removes), the open-questions statement, the unconditional-finalize/conditional-owner paragraph with the never-hand-roll prohibition, and a note on the self-referential hazard that this plan's own finalize exercises the function it changes. V-03(b) records the three fixture prerequisites and the HEAD baseline |
| PR-906 | MEDIUM | IN-SCOPE | Project rules (`aw check`) | `aw check` reported two findings against this plan: `check.lifecycle-transition-invalid` with detail `recorded lifecycle transition 'to-review' -> 'draft' is invalid: missing predecessor: backwards transition`, and `check.ipd-uncarried-obligation` with `1 obligation(s) name no durable carrier`. Inspection: the history listed `draft` below `to-review` in a newest-first section, and none of the four `## Deferred` rows carried a carrier line | **The plan trips the repository's own consistency checker twice.** Both are pre-existing. A plan carrying `Blocks-Release: next` cannot be approved while failing the checker it ships, and the uncarried-obligation finding is substantive rather than cosmetic: the `plans_refs` row names a measured live defect that would have vanished from the attention view when this plan reached `executed` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The redundant `draft` record is removed and its content folded into the `to-review` record (accurate, since the plan was authored in one turn). Backlog `eeiytw` filed from F-12's measurement and cited as `Carrier: eeiytw` on the `plans_refs` row; the other three rows carry `Carrier-Declined:` reasons (a rejected alternative, a deliberately-kept parser, a clean audit result). Both findings verified cleared by `aw check`. F-18 and the Scope check record it |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-902: should E-02 render every drift finding, or only those that drove the nonzero verdict? | Filter to `severity != "info"`, the same predicate `drift_exit_code` uses | (a) render everything, as the replaced print did; (b) render nothing and point at `aw index plans --check`; (c) render everything but label the advisory ones | Option (a) inherits a set the print chose for a different purpose: the print dumped a check's output, while this message explains a REFUSAL, so an advisory finding named there is actively misleading about the cause. Measured, a tree can carry `info` findings and converge (rc 0), so the two sets genuinely differ. Option (b) is HEAD's behavior and is the defect E-02 exists to fix. Option (c) puts severity-rendering into an exception message for no operator benefit, since advisory findings are by definition not actionable for this refusal. The chosen filter also makes message and verdict provably consistent, reading one field through one test | yes |
| D-2 | PR-901: the path half of E-03(d) is vacuous. Drop the path assertion, or relocate it? | Key the discriminating assertion on the RULE NAME; permit a path assertion only against the `summary` or diagnostic `detail` | (a) drop any path assertion entirely; (b) keep it as written against the serialized payload; (c) assert the path is absent at HEAD as a control | Option (b) is the finding. Option (a) is tempting and loses something real: the operator value of E-02 is that a human reading the refusal learns WHICH plan drifted, so a test that never checks the path stops guarding the feature's point. Option (c) would encode a HEAD-specific accident (that the id6 happens to appear via the diagnostic location) as an expected absence, which breaks the moment an unrelated field carries the path. Scoping the path assertion to the fields E-02 actually writes keeps the guard and removes the vacuity | yes |
| D-3 | PR-906: the plan trips `aw check` twice. Fix in place, or record and let the executor handle it? | FIX BOTH IN PLACE, and file the one real residual defect as backlog `eeiytw` | (a) record both as findings and leave the plan failing the checker; (b) fix the history order only and leave the carrier rows, since `aw ipd lint` passes without them | Option (a) is refused because the plan carries `Blocks-Release: next`: approving a release-gating plan that fails the repository's own consistency checker asserts a cleanliness that does not hold, and the plan-review workflow's own instruction is to fix by default. Option (b) misreads the uncarried-obligation finding as cosmetic; it is substantive, because the `plans_refs` row names a defect measured live in F-12 that would have silently vanished from the attention view once this plan reached `executed`, which is precisely what the carrier mechanism exists to prevent. Filing `eeiytw` from F-12's own measurement discharges it with evidence rather than a placeholder | yes |
| D-4 | PR-903: is a fourth verdict-equivalence tree worth the executor's time, given review already measured it agrees? | YES, require it | (a) record review's measurement in Findings and let V-01 keep three trees; (b) require it and mark it expected-to-agree | Option (a) was the tempting shortcut and it defeats the purpose of V-01, which is that the EXECUTOR re-derives rather than trusting an authoring or review number; the plan is already explicit about that for its test baselines. The `info` case is also the one where a future change to `check_drift`'s enrichment could silently break equivalence, so it is the tree most worth having in the permanent evidence. It is recorded as expected-to-agree (which is option (b) folded in) so the executor is not hunting a phantom divergence | yes |
| D-5 | Should the review implement E-01, having measured the replacement verdict-equivalent and silent on four trees? | NO; the probes stay throwaway scratch | (a) land the two-line change, since it is fully measured; (b) paste the probe's replacement snippet into E-01 as the implementation | The workflow edits planning documents only, and this is the most load-bearing write in the toolkit on a plan carrying `Blocks-Release: next`. The probe also proves less than it appears: it called the candidate path directly rather than editing the function, so it never exercised the real call site inside a transaction, and it asserted nothing about the `RuntimeError` message E-02 must build. Option (b) would freeze probe-grade argument handling into an executable contract. What the probes legitimately contribute is the six findings plus confirmation that E-01's approach is verdict-equivalent, silent, and buildable | yes |
