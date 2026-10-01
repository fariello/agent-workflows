# Review findings: plan iocyf3

- Subject-Id: iocyf3
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-P01 (HIGH, fixed), PR-P02 (HIGH, fixed), PR-P03 (HIGH, fixed), PR-P04 (MEDIUM, fixed), PR-P05 (MEDIUM, fixed), PR-P06 (MEDIUM, fixed), PR-P07 (MEDIUM, fixed), PR-P08 (LOW, fixed), PR-P09 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `170368788`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, two `IPD-Z602` advisories on E-04 and E-06);
`--phase review-finalize --agent` now reports `clean` with ZERO findings. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply.

I BUILT THE WHEEL RATHER THAN TRUSTING THE PLAN'S BUILD, because the plan's whole shape (restore a guard
rather than weaken the prose) rests on that one measurement. It reproduces:

- `python3 -m build --wheel` succeeds in 2.09s and 2.57s on two runs, producing a 356-entry wheel.
- Applying the deleted file's own `FORBIDDEN_TOP`, `FORBIDDEN_AGENTS_SUBSTRINGS` and `FORBIDDEN_FILES`
  yields `FORBIDDEN VIOLATIONS: 0`. The package is present and 161 entries sit under
  `agent_workflows/_data/.aw/system`.
- The wheel's `METADATA` declares `Requires-Dist: filelock>=3` unconditionally plus four `; extra == 'test'`
  entries, exactly as F-3 states.

Everything else material also verifies: `tests/test_packaging.py` is absent and `19313eed` deleted it; both
quoted `CONTRIBUTING.md` strings are present; no surviving test matches `force-include` or `hatch.build` (the
only tree hit is a JSON fixture); the deleted file contains zero `slow` occurrences and no `pytestmark`;
`conftest.py`'s `_DEFAULT_TEST_TIMEOUT` is 90.0; `PIP_NO_INDEX=1` fails the isolated build and `hatchling` is
absent from the test interpreter so `--no-isolation` is unavailable; `tests/test_packaging.py` is in
`leak_sanitizer`'s allowed paths; and `76ic0k` edits a different `CONTRIBUTING.md` section, so F-9's
no-collision judgement is right.

THIS IS A WELL-MEASURED PLAN AND ITS CENTRAL JUDGEMENT IS CORRECT. The findings below are four things the
plan did not measure and three stale or self-contradicting statements, not a disagreement with its approach.

PR-P01 is the one that would have shipped a false document. E-05 corrects two claims, and there is a THIRD in
the same bullet: the sentence E-05 deliberately KEEPS (because E-02 makes its citation true) ends
`...or the meta docs, and that no runtime dependency is declared.` That clause is false on exactly the
evidence F-3 already gathered, and it is worse than the original defect would have been, because after E-02
and E-03 the paragraph would cite a test that EXISTS while misdescribing what that test asserts: E-03 pins
the dependency set to `{"filelock"}`, not to empty. So the plan would have produced a document making a false
claim about this plan's own deliverable. E-05 now carries three labelled claims, and V-05 requires a search
proving BOTH false strings are absent afterwards, since the second is easy to miss while editing the first.

PR-P02 is a false finding the plan built an E-item on. F-5 asserts that the deleted `FORBIDDEN_TOP`'s
substring `workflow-artifacts/` flags the legitimately shipped
`agent_workflows/_data/.aw/system/workflows/templates/workflow-artifacts-README.md`, and E-03 was written to
avoid that. Measured on the real wheel: the filename carries a HYPHEN and the token carries a SLASH, so
`"workflow-artifacts/" in "...workflow-artifacts-README.md"` is `False`, and matching all of `FORBIDDEN_TOP`
as a BARE SUBSTRING over the 356 entries yields ZERO hits, identically to `startswith`. The trap is real but
narrower: it fires only if a restorer LOOSENS the token by dropping its trailing slash. This matters beyond
tidiness because E-03 told the executor to record the measurement in a comment, and the comment as specified
would have told the next author that substring matching is unsafe here, misdirecting them away from the edit
that is actually dangerous. F-5 is corrected in place, E-03 is rewritten to prefer `startswith` and forbid
loosening a token, and V-03 now fails the item if the comment repeats the overstated claim.

PR-P03 corrects a factual error in F-8 that OQ-02's reasoning rests on. Both assert `1jg2m2` is
`- Status: to-review`, and OQ-02 argues against an `- Item-Dependencies:` edge partly because an edge would
gate this plan behind "an unrelated chore's entire review-and-execution cycle" and "could strand it
permanently if that plan is never approved". Measured: `1jg2m2` is `- Status: reviewed` with
`- Readiness: go-pending-approval`, which is strictly AHEAD of this plan. The no-edge conclusion survives on
the grammar argument alone, which is the load-bearing half, but a reader checking the stated basis would find
it false, and the practical reading inverts: `1jg2m2` is likely to execute FIRST, which E-05's branch must
handle as the expected case rather than the contingency.

PR-P04 is a measurement that makes the coordination question safer than the plan claims. `1jg2m2` E-08 adds
`tests/test_docs_test_citations.py`, scanning every file under `docs/` plus an enumerated list that includes
`CONTRIBUTING.md`, failing on any `tests/test_*.py` citation that does not exist. Evaluating both orders: if
`1jg2m2` lands first its edit removes the citation and the guard is green; if THIS plan lands first the
citation exists again because E-02 restored the file, and the guard is also green. So neither order produces
a red guard, and this plan's restoration additionally gains a durable keeper that will catch a future
re-deletion. Recorded as F-13 and folded into OQ-02, because it converts a stated risk into a measured
non-risk.

PR-P05 sharpens OQ-01 without usurping it. The question weighs the `slow` marker partly on the ground that a
marked guard would still run in "CI's advisory slow step". That step carries `continue-on-error: true`, so a
failure there does not fail the build. A `slow`-marked guard therefore runs in NO blocking gate anywhere: not
the routine suite (deselected by `addopts`), not the lane-integration suite, and not blockingly in CI. I did
NOT resolve the question, because which way that tradeoff falls is a risk-appetite call about the default
suite and the plan correctly assigns it to the maintainer; I recorded the corrected cost (F-15) in OQ-01, in
E-04, and at the gate so an approving maintainer sees it.

PR-P06 is the delta-bar problem this sweep keeps finding. E-06 and V-06 compare against a baseline but do not
acknowledge that the baseline is red: bare `python3 -m pytest` on an unmodified tree reports
`1 failed, 3431 passed, 2 skipped`, the failure being
`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a filed
local-versus-UTC history-clock defect owned by backlog `fnb8pl`. The plan's failing-node-id framing was
already the right instrument, which is to its credit; it just needed the expected failure named so an
executor neither investigates it nor reads it as a regression nor claims a green suite.

PR-P07 is an internal contradiction in the front matter. `- Scope:` states this plan "coordinates by
`- Item-Dependencies:`" with `1jg2m2`, while `- Item-Dependencies:` reads `none` and OQ-02 resolves at length
that no edge should be declared. An executor reading the scope line would look for an edge that deliberately
does not exist.

PR-P08 and PR-P09 are smaller. The gate instructed moving the plan to `executed/` "via the tooled transition"
unconditionally, but the RUNNER owns that transition under `aw oc run` / `aw agy run`; rewritten to the house
conditional-owner form. And the two `IPD-Z602` density advisories on E-04 and E-06 were cleared by moving
rationale into sub-bullets rather than splitting either item, since "decide the marker" and "run the
regression pass" are each one concern.

ONE THING WORTH RECORDING IN THE PLAN'S FAVOUR. F-17 notes something the plan undersells: the deleted file
already contains E-03's assertion almost verbatim, including the extras exclusion, the two-sided equality
that catches both a silent ADD and a silent DROP, and the D138 reasoning in comments, and its `setUpClass`
already implements E-02's two-case environment handling exactly as specified. So E-02 and E-03 are recoveries
with a known-good source rather than design tasks, which lowers their risk materially.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-P01 | HIGH | UNDER-SCOPE | F. KISS, principles and UX (honest documentation) | `CONTRIBUTING.md`'s "Build a wheel" bullet, clause `and that no runtime dependency is declared.`; built wheel `METADATA` `Requires-Dist: filelock>=3` | A THIRD false claim sits in the same bullet and E-05 does not name it. Worse than the original defect: after E-02/E-03 the paragraph would cite a test that exists while misdescribing what it asserts, since E-03 pins the set to `{"filelock"}` rather than to empty. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11. E-05 restructured into three labelled claims with the third named and its remedy stated; V-05 requires a search proving BOTH false strings absent afterwards; `- Scope:` and the Proposed changes list updated from "two" to "three". |
| PR-P02 | HIGH | IN-SCOPE | D. Anti-regression (a finding that is false) | F-5 versus measurement: `"workflow-artifacts/" in "...workflow-artifacts-README.md"` is `False`; bare-substring match of `FORBIDDEN_TOP` over the 356-entry namelist yields 0 hits, same as `startswith` | F-5's substring trap is FALSE as filed (hyphen versus slash), and E-03 was built on it. The specified comment would have told the next author that substring matching is unsafe here, misdirecting them from the real hazard, which is loosening the token to a slash-less form. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 corrected in place with the re-measurement and the narrowed true statement. E-03 rewritten to prefer `startswith`, forbid loosening a token, and record the corrected measurement. V-03 now fails the item if the comment repeats the overstated claim. E-02's cross-reference reworded. |
| PR-P03 | HIGH | IN-SCOPE | G. Plan executability (false premise in a resolution) | `1jg2m2` front matter: `- Status: reviewed`, `- Readiness: go-pending-approval`, plus its 2026-09-30 `/plan-review` history line | F-8 and OQ-02 both assert the contending plan is `to-review` and build the no-edge argument partly on that plus a stranding risk. It is `reviewed`/`go-pending-approval`, AHEAD of this plan, so that half of the reasoning is false and the practical ordering inverts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12. F-8's status corrected, OQ-02's false half removed with the correction recorded, the authoring history line's parenthetical corrected, and the gate now states the other plan may execute first. The no-edge conclusion is retained on the grammar argument. |
| PR-P04 | MEDIUM | IN-SCOPE | C. Architecture and operability (coordination) | `1jg2m2` E-08 scan list including `CONTRIBUTING.md`; its F-11 census | The plan treats the ordering as a risk to manage. Measured, NEITHER order breaks `1jg2m2`'s new citation guard: its edit removes the citation, or this plan restores the file the citation names. The coordination result is stronger than the plan claims, and the restoration gains a durable keeper. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13 and folded the measurement into OQ-02 and the gate, converting a stated risk into a measured non-risk. |
| PR-P05 | MEDIUM | IN-SCOPE | E. Testing and verification (a gate that gates nothing) | `.github/workflows/tests.yml`: the slow step carries `continue-on-error: true`; the blocking step inherits `-m 'not slow and not livecorpus'` | OQ-01 weighs "marked" partly on the guard still running in CI's slow step. That step is advisory, so a `slow`-marked guard would be non-blocking in every gate. The "marked" option costs more than the question states. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15 and recorded the corrected cost in OQ-01, in E-04's weighing bullet, and at the gate. Deliberately NOT resolved: the tradeoff is a maintainer risk-appetite call, and the plan correctly assigns it. |
| PR-P06 | MEDIUM | UNDER-SCOPE | E. Testing and verification | measured bare run `1 failed, 3431 passed, 2 skipped`; backlog `fnb8pl` | E-06 and V-06 compare against a baseline without acknowledging the baseline is red, so an executor would investigate an unrelated filed defect or read it as a regression. The node-id framing was already correct and only needed the expected failure named. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-16; E-06, V-06 and the validation list name the `fnb8pl` failure as expected in both runs, forbid investigating or fixing it, and forbid claiming a green suite. |
| PR-P07 | MEDIUM | IN-SCOPE | G. Plan executability (self-contradiction) | `- Scope:` "coordinates by `- Item-Dependencies:`" versus `- Item-Dependencies: none` and OQ-02's "DECLARE NO EDGE" | The scope field claims a coordination mechanism the plan deliberately does not use, so an executor would look for an edge that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14. `- Scope:` rewritten to state the contention plainly and to name the re-read-and-branch mechanism, explicitly noting `- Item-Dependencies:` is `none` by design. |
| PR-P08 | LOW | IN-SCOPE | G. Plan executability (execution contract) | the gate's "move this plan to `.aw/records/plans/executed/` via the tooled transition" | Stated unconditionally, but the RUNNER owns the transition under `aw oc run` / `aw agy run`, so an executor obeying it would duplicate or race the runner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to the house conditional-owner form; hand-edited status lines and hand-rolled `git mv` stay forbidden. |
| PR-P09 | LOW | IN-SCOPE | F. KISS (right-sizing presentation) | `aw ipd lint --phase author` reported `IPD-Z602` on E-04 and E-06; `ipd_schema.e_item_density_advisory` named three clauses in each | Two E-items tripped the density advisory by carrying their rationale inline as chained clauses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rationale moved into sub-bullets on both, keeping one action sentence each. Neither was split: "decide the marker" and "run the regression pass" are each one concern. `e_item_density_advisory` now returns `None` for all six E-items and the lint reports zero findings. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | A third false claim sits in the bullet E-05 keeps. Correct it here, or file it separately? | Correct it in E-05, which already owns that paragraph. | File a separate backlog item (leaves a known-false sentence shipping, and in the same bullet this plan is editing); leave it and let the citation fix stand alone (the paragraph would then misdescribe this plan's own deliverable). | The clause is in the SAME bullet and the SAME edit site E-05 already opens, so correcting it adds no new scope path and no new risk, while leaving it would publish a false claim about the restored test. `CONTRIBUTING.md` is already declared in `- Scope-Paths:`. | yes |
| D-2 | F-5's substring trap does not reproduce. Delete the finding, or correct and narrow it? | Correct it in place and narrow E-03 to the real hazard (a loosened, slash-less token). | Delete F-5 and drop E-03's anchoring instruction (loses a real, if narrower, hazard); leave F-5 as written (ships a comment that misdirects the next author). | Measured on the built wheel: the slash-bearing token yields 0 hits under BOTH `startswith` and bare substring matching, while the slash-less token `workflow-artifacts` does hit the shipped template. So a hazard exists but is reached by a different edit than F-5 named, and the honest fix is to name that edit. | yes |
| D-3 | OQ-01 is open with `Owner: maintainer`. Resolve it from evidence, or leave it open? | Leave it OPEN and record the corrected cost. | Resolve it unmarked (authoring's lean, and my measurement supports it); resolve it marked. | The workflow requires resolving from evidence rather than asking, but `AGENTS.md` reserves risk-appetite calls for the human, and this one trades a network-outage risk to every concurrent lane against guard coverage. It is also genuinely non-blocking: E-04 decides at execution with numbers and V-04 refuses to pass without them, so nothing vanishes. What I owed was the corrected cost (F-15), not the decision. | yes |
| D-4 | Two E-items trip the density advisory. Split them, or restructure? | Restructure into sub-bullets. | Split E-04 into measure-then-decide; split E-06 into suite, cleanup and leak-gate items. | Each is one concern executable in one pass: E-04 produces a single marker decision, and E-06 is a single end-of-plan verification pass whose parts share one tree state. Confirmed by re-running `ipd_schema.e_item_density_advisory`: `None` for every E-item, and `aw ipd lint --phase review-finalize` reports zero findings. | yes |

No `Reversible: no` decision was taken in this round, so no escalation is owed under the irreversible-decision rule.

### Escalations

None. Every finding is `FIXED`, so no finding at or above the `HIGH` gate threshold is left `OPEN` or
`DEFERRED`. OQ-01 remains `- Blocking: no` and does not gate readiness (maintainer ruling of 2026-09-10,
plan `qhy3i3` OQ-01).
