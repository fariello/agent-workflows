# Review findings: plan mvcwsd

- Subject-Id: mvcwsd
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `8dc7ed99` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent` conforms after
revision. `IPD-S407` does not apply: the plan's own first `- Kind:` bullet reads `child`. No pre-review
snapshot was owed: the plan was committed and unmodified, `git status --short` empty at review start.

NO PRODUCTION FILE AND NO EXISTING TEST WAS MODIFIED BY THIS REVIEW, and NOTHING WAS WRITTEN TO
`.aw/records/` BY ANY PROBE. Every measurement was a read, an in-process call, or a throwaway pytest
plugin under a gitignored `tmp/` path, all removed afterwards (`git status --short` empty before commit).
That matters here specifically, because the plan's own V-02 proposed writing into the live shared tree and
I wanted to establish that the trap can be proven without doing so (which became PR-503).

THIS PLAN IS THE BEST-MEASURED ARTIFACT I HAVE REVIEWED IN THIS SWEEP, and its central judgement is
right. It re-swept its own backlog item's inventory rather than trusting it, found four of six named call
sites in files a trim commit deleted, IMPLEMENTED BOTH candidate detector mechanisms before choosing
between them, and then REFUSED the enforcement half the item asked for with numbers rather than with
preference. I re-derived every load-bearing claim independently. CONFIRMED:

- **F-01** exactly. `tests/test_plan_readiness.py` does not exist; `git show 19313eed --stat` lists it at
  `2548 ----` and `tests/test_cli_find.py` at `688 ----`; the replacement is 122 lines; neither
  `test_a_setid_query_excludes_prefix_sharing_foreign_sets` nor
  `test_an_id6_query_returns_the_declaring_artifact_not_its_citers` appears anywhere in `tests/`; and the
  three claimed survivors are present (`tests/test_ipd_lint.py` lines 731 and 1096,
  `tests/test_ipd_schema.py` line 2986).
- **F-02's DIRECTION AND KIND**, though not its absolute numbers (PR-504). A review-written runtime audit
  probe found `tests_reading_live=42`, `marked=0`; two review-written AST sweeps found 31 (loose) and 19
  (tight). All four measurements agree the runtime population strictly exceeds the syntactic one and that
  the misses are tests reaching the tree through a helper or through production code.
- **F-03** entirely. All seven named example tests exist and every one appears in my runtime census.
- **F-04**, which is the plan's sharpest finding, reproduced independently. Running
  `tests/test_ipd_set_plan.py` alone under my probe gave `prefix_only_events=0 resolve_needed_events=2062`
  (1031 per test), so a prefix-only detector sees ZERO of that module's live reads. Suite-wide the split is
  `prefix_only=47728 resolve_needed=2858`, so the fallback matters for about 6 percent of events overall
  and for 100 percent of that module's.
- **F-05's mechanism**, proven in-process without touching the live tree:
  `ipd_lint.check_readiness_attestation` returns `[]` when `_REVIEW_EVIDENCE_RE` matches the history and
  `IPD-M107` otherwise, and on a synthetic document carrying `- Readiness: go-pending-approval` with only a
  `draft` history line it returned `['IPD-M107']`. The sweep body is
  `for plan in sorted((REPO_ROOT / SOURCE_PLANS).rglob("*.ipd.md"))`, which is what converts that into a
  suite failure.
- **F-07 and F-15**. `python3 -m pytest -m ''` gave `3 failed, 3450 passed, 2 skipped, 3 warnings in
  94.68s`, failing exactly the three tests the plan names as CI-tracked advisories. The arithmetic also
  checks out: 3455 collected minus 5 `livecorpus` equals the 3450 the default run reports deselected.
- **F-09 BOTH HALVES**, each with a probe I wrote. A section appended in `pytest_runtest_makereport` inside
  a worker printed in full under `-n 2` (header plus all three sample paths). A counter accumulated in a
  worker reported 0 from the coordinator.
- **F-10** exactly, including the hazard. `tests/test_walkthrough_id6.py` asserts `len(all_files) == 24`;
  the tree holds 25 `.md` files of which one is `README.md`, so 24 non-README, and the test passes today
  and reds on the next walkthrough. Backlog `zf1m48` exists and is open.
- **F-11** exactly, count and membership. `-m livecorpus --collect-only` reports
  `5/3455 tests collected (3450 deselected)` and the five node ids are precisely the three
  `TestProbePayloadLiveCorpus` cases plus the two the plan names.
- Every convention claim: `conftest.py:37` is `pytest_plugins = ["tests.deselect_notice"]`;
  `tests/deselect_notice.py` uses `workeroutput`; `tests/test_run_viewer.py` carries two `sys.addaudithook`
  registrations; `conftest.py` records `31 failed, 8080 passed` versus `0 failed, 7993 passed` for the role
  block; `pyproject.toml` defines the `livecorpus` marker with the 2026-09-19 incident verbatim and
  `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`; `GUIDING_PRINCIPLES.md:172`
  and `:180` carry P16's prohibition and its one narrow exception as quoted. The three sibling plans
  (`b02ohu`, `76ic0k`, `kmzude`) exist, and `76ic0k` E-04 does add exactly the `CONTRIBUTING.md` pointer
  bullet the plan says it does. None of the three collides with this plan's declared paths.

SIX FINDINGS WERE RAISED AND ALL SIX FIXED. One is HIGH because the plan asserted a measured figure that
re-measurement contradicts, and two more would each have made an executor's own measurement unrunnable or
unsafe.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | HIGH | IN-SCOPE | Rubric E (verification); G (honest measurement) | plan F-08 as authored; six review summary lines | F-08 claimed always-on costs "roughly 2 to 4 seconds on a 46 second suite" from three runs each way. RE-MEASURED AT REVIEW THE ORDERING INVERTED: without the plugin 47.16/50.22/50.78s, with a prototype of the E-01/E-02 shape 48.07/46.85/47.27s, so instrumented runs were FASTER on average. The spread WITHIN the uninstrumented set alone was 3.62s, larger than the effect authoring claimed to measure, so three runs cannot establish even the SIGN of the difference. The plan's CONCLUSION (always-on is affordable) is unaffected and arguably strengthened; what fails is the specific number, which E-05(c) and V-05 then ask the executor to re-derive and compare against. A figure that was never resolvable is a bad acceptance baseline, and OQ-02's framing rested on it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 restated as a bound BELOW THE NOISE FLOOR with both measurement sets and both within-set spreads, explicitly retracting the point value. Recorded as F-12. E-05(c) now forbids reproducing the retracted figure and requires either enough runs to beat the variance or the honest bound. V-05 now requires the spread pasted, not only the six times. OQ-02's rationale updated to note the price is cheaper than the question assumed while taking no position on the question. |
| PR-502 | HIGH | IN-SCOPE | Rubric E; G (executability) | probe under bare `addopts` -> `tests_reading_live=0`; same probe single-process -> `42` | E-05(b) instructs measuring "THE RUNTIME POPULATION in the same bare default run". That is UNRUNNABLE as written, because F-09's own xdist boundary applies to the plan's MEASUREMENT as well as to its deliverable: a census accumulated in a worker does not reach the coordinator. Measured, the probe reports 0 under the configured `-n auto` and 42 single-process. An executor following the instruction literally would record "no test reads the live tree", the exact inverse of the plan's thesis, and would have no reason to doubt it. The plan drew this consequence for its deliverable (correctly choosing `report.sections`) but not for its own probe. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05(b) now states in bold that single-process collection must be forced or the answer is zero, with both measurements, and requires the invocation pasted. V-05 now treats an unqualified zero as a broken probe rather than a finding. Recorded as F-13. Added a paragraph to Required tests distinguishing the measurement probe (must not run under `-n auto`) from the deliverable (which does cross the boundary). |
| PR-503 | MEDIUM | IN-SCOPE | Rubric B (safety); F (UX of a shared checkout) | plan V-02 as authored; in-process `check_readiness_attestation` -> `['IPD-M107']` | V-02 instructed the executor to `aw ipd scaffold` a throwaway plan INTO the live `.aw/records/plans/pending/` and delete it, in a checkout the plan's own gate warns may be shared with other agents. The trap MECHANISM does not require that: driving `check_readiness_attestation` in-process on a synthetic document reproduces `IPD-M107` with zero shared writes, which I did at review. The attached-note half does need a real failing test in a real run, but a temp-dir test reading a fake guarded root (the E-04(c) shape the plan already specifies) serves it. So the riskiest instruction in the plan was also the avoidable one. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | V-02 restructured: the isolated in-process route is now PREFERRED and specified with the measured evidence, the temp-dir failing test is preferred for the attached-note half, and the live-tree route is an explicit FALLBACK carrying before-and-after `git status --short` requirements. The gate's shared-checkout paragraph rewritten to match, and it now also notes that the sweep is currently GREEN with attested `Readiness` plans present, so its passing is not evidence the trap is absent. Recorded as F-14. |
| PR-504 | MEDIUM | IN-SCOPE | Rubric G (live-artifact criteria) | three AST sweeps yielding 4, 19 and 31 | F-02 states the AST approach "finds 4" as though it were a property of the tree. It is a property of the SWEEP: two independently written review sweeps found 31 (matching any `glob`/`rglob`/`iterdir` whose call text mentions `.aw`/`records`) and 19 (requiring a repo-root-anchored or literal `.aw/records` base and excluding tmpdir hints). The plan's central argument is a RATIO (4:38), and if the numerator moves by a factor of five with the heuristic, the ratio cannot be quoted as measured fact. Notably this STRENGTHENS the underlying argument in a way the plan did not claim: a guard whose population depends on its own strictness is itself untrustworthy, which is the item's stated worry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 rewritten to report all four measurements, to state that the AST number is sweep-dependent and not a tree property, and to identify what IS robust (the direction and the kind of miss). F-03's "missed 34" reworded to separate the count from the membership. E-05(a) now requires the sweep's criterion recorded beside its count and forbids a bare number. V-05 likewise. |
| PR-505 | MEDIUM | UNDER-SCOPE | Rubric G (execution contract) | plan gate as authored | The gate was strong (it already carried the commit path-scoping, the never-push rule, staged-set verification, the enforcement prohibition, and a measure-do-not-transcribe paragraph) but was missing three required elements: an explicit SCOPE FENCE enumerating what must not be touched, the hard-MUST honesty rule (paste the ACTUAL runner output), and the lifecycle transition with conditional runner/executor ownership. The lifecycle wording said only "do not move this plan to executed/ ... use the tooled transition", which does not name who performs finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the honesty rule and the UNPIPED exit-code rule. Added a SCOPE FENCE worded as a DECLARATION for the runner to reconcile (per the 2026-09-01 ruling, not a stop directive) with six negative constraints, each closing a specific wrong turn: no marking or allowlist or failing, no `pyproject.toml`, no `CONTRIBUTING.md`/`GUIDING_PRINCIPLES.md` (both owned by live siblings), `conftest.py` only in its `pytest_plugins` list, no touching the two carried census tests or any of the 42 census tests, and no source-reading test of the plugin's own docstring. Added the LIFECYCLE TRANSITION paragraph with conditional ownership, naming `AW-LIFECYCLE-ROLE-001`, and noting that the OQ-02-NO disposition is `not-executed` and must NOT route through finalize. Added approver-facing summary and scrutiny paragraphs. |
| PR-506 | LOW | IN-SCOPE | Rubric G (live-artifact criteria) | eleven sites quoting `38` as settled | `38` was used throughout the plan (Concern, Scope, E-02, F-06, bound (c), Deferred, Scope check, OQ-01, the gate) as a settled population, and it is a live figure that review measured at 42. None of these is an acceptance criterion, so no `V-*` needed loosening, but a reader meeting "the 38 tests" in nine places will treat it as fixed, and the plan's own gate warns against exactly that transcription habit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All eleven sites restated as a re-derivable range ("38 at authoring, 42 at review") or as a qualitative population ("the corpus-reading tests", "dozens"), preserving each sentence's argument. Two further per-test event counts (943 events, the F-09 3,834) similarly annotated with both measurements. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-08's overhead figure contradicts re-measurement. Should the plan be failed on it, the figure corrected to the review numbers, or the claim weakened to what the data supports? | Weaken the claim to a noise-floor bound, retract the point value, and forbid E-05(c) from reproducing it. | (a) Substitute the review numbers as the new measured figure: REJECTED, because they would assert that the plugin makes the suite FASTER, which is equally unsupportable and obviously an artifact of variance. (b) Fail the plan on an unsupported measurement: REJECTED as disproportionate, since the plan's CONCLUSION survives (the cost is small either way) and the plan itself labelled the figure a range "because three runs on a loaded machine do not support a tighter claim", so it was already hedging in the right direction. (c) Leave it and let E-05 discover the problem: REJECTED because V-05 as written demands a comparison against the retracted figure, so the executor would be asked to reconcile with something unreconcilable. | Six review runs (47.16/50.22/50.78 uninstrumented, 48.07/46.85/47.27 instrumented), within-set spread 3.62s versus a claimed 2-to-4s effect. Identical `3246 passed, 2 skipped` throughout, so nothing else differed. | yes |
| D-2 | V-02 instructs writing a throwaway plan into the live shared `.aw/records/`. Should that be forbidden, made conditional, or left as written with the existing care instructions? | Make the isolated route PREFERRED and the live-tree route an explicit fallback with before-and-after cleanliness evidence. | (a) Forbid the live-tree reproduction outright: REJECTED, because seeing the note ATTACHED to a genuine corpus-trap failure is real evidence that an in-process predicate call cannot give, and forbidding it would weaken the validation. (b) Leave it as written: REJECTED, because the plan's own gate says the checkout may be shared and another party's work must never be disturbed, so instructing a live write as the DEFAULT when a zero-risk route proves the same mechanism is an unnecessary hazard. (c) Require a scratch clone: NOT taken, as heavier than needed and not an established pattern in this repository's test conventions. | Measured in-process: `check_readiness_attestation` on a synthetic doc returns `['IPD-M107']`, reproducing the trap with no write. The sweep's body rglobs the real tree, which is the link from diagnostic to suite failure. The plan already specifies a temp-dir failing-test shape in E-04(c) that serves the attached-note half. | yes |
| D-3 | Does OQ-02 being `open` with `Owner: maintainer` make this plan `NO-GO`? | No. Readiness is `GO - PENDING HUMAN APPROVAL`; OQ-02 is left open and untouched. | (a) Mark `NO-GO` because a question is open: REJECTED by the controlling rule, which changed the first `NO-GO` condition to an unresolved BLOCKING question on the 2026-09-10 maintainer ruling (plan `qhy3i3` OQ-01); OQ-02 carries `- Blocking: no`. (b) Resolve OQ-02 myself: REJECTED outright, and this is the important one. It asks whether a permanent suite addition is worth its cost given nothing is broken today, which is a priority and risk-appetite judgement reserved to the maintainer; a reviewer answering it would be inventing a human decision. (c) Flip it to `Blocking: yes` to force an answer: REJECTED, because the plan is technically executable as written, so the question gates SPENDING rather than correctness, and mislabelling it would hold a sound plan on a question its own author correctly judged non-stopping. | The plan-review readiness rule's `NO-GO` conditions and the 2026-09-10 ruling. OQ-02's own `- Blocking: no` and `- Owner: maintainer`. The review found no unfixed BLOCKER or HIGH and the verdict is APPROVE WITH REVISIONS APPLIED, so the clean bar is met. | yes |
| D-4 | The AST count varies 4 / 19 / 31 across three implementations. Does that undermine the plan's refusal of the item's gate? | No; it strengthens it, and F-02 now says so explicitly rather than quoting a single ratio. | (a) Treat the variance as a defect in the plan's evidence and require one authoritative count: REJECTED, because no such count exists; "a glob whose base is a live-records root" is inherently a heuristic and every implementation draws the line differently. (b) Drop the AST measurement entirely: REJECTED, because the COMPARISON is the plan's argument and removing half of it would leave the refusal unevidenced. (c) Quote only the tightest sweep: REJECTED as cherry-picking the number most favourable to the plan's thesis. | Three sweeps measured: authoring 4, review loose 31, review tight 19; runtime 38 authoring / 42 review. All agree the runtime population strictly exceeds the syntactic one and that the misses share a KIND (helper-mediated or production-code-mediated reads), which is `utwr6y` E-03's stated evasion route. | yes |

No `Reversible: no` decision was made, so no escalation under the irreversible-decision rule is owed.
No finding was left `OPEN` or `DEFERRED`, so no escalation to a `- Blocking: yes` question under
`review_findings_gate.block_at` (default `HIGH`) is owed; both HIGH findings were FIXED. OQ-02 remains
open by design and is not a finding escalation: it is a pre-existing question the review deliberately did
not answer (D-3).

### Checklist assessment (required for an agent-executable IPD)

The CREATOR authored both checklists and the E/V bijection is 1:1 with concrete per-item evidence demands.
Right-sizing: six E-items in two task groups, each one concern. E-01 and E-02 correctly split the DETECTOR
from the REPORTING channel, which is the right seam because they have different failure modes and V-01
versus V-02 test genuinely different properties (path soundness versus section delivery). E-05 and E-06
are both docstring writes and could arguably merge, but they are kept apart for a defensible reason: E-05
is a MEASUREMENT that may contradict the plan while E-06 is a TRANSCRIPTION that must not, and folding
them would invite an executor to soften a bound under measurement pressure. `aw ipd lint` reported no
`IPD-Z602` density advisory at either checkpoint. No split is recommended.

TWO STRUCTURAL STRENGTHS WORTH NAMING, because they are the reason this plan needed correction only at the
edges. FIRST, E-04(c) requires a SUBPROCESS self-test and V-04 requires proving it FALSIFIABLE by
neutering the section-append and showing (a) and (b) still pass while (c) fails. That is precisely the
anti-vacuity discipline most plans omit, and the plan cites the prior measurement (`swps4w` F-6) that
establishes why an in-process self-test cannot cover the reporting branch. SECOND, E-06 writes the
detector's four BOUNDS into its own docstring, including that it is not a gate and that the 2026-09-19
incident would recur with a better message. A deliverable documenting what it does not do is rare and is
the correct response to the plan's own observation that an overclaimed diagnostic is worse than a narrow
one. V-06 goes further and requires bound (b) DEMONSTRATED rather than merely asserted.

The checklist's weakness was that two of its own MEASUREMENTS were unrunnable or unsafe as specified
(PR-502, PR-503) and one asked for reconciliation against an unsupportable figure (PR-501). All three are
repaired in place. Note the asymmetry the plan states and I confirm: E-05(a)'s AST census is a measurement
pasted into evidence and a docstring, never an assertion, so P16's production-source prohibition is not
engaged, and GUIDING_PRINCIPLES.md:180's narrow exception is not even needed.

Live-artifact convention: this plan is almost entirely live populations, and it handled them better than
most (it required re-derivation in E-05 before review said anything). The residue PR-506 fixed was
rhetorical: `38` appearing in nine prose sites as though settled. No `V-*` used a population count as a
bar, so no acceptance criterion needed loosening.
