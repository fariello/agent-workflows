# Review findings: plan xdvglg

- Subject-Id: xdvglg
- Subject-Type: ipd
- Reviewed-At: 2026-09-18
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `2c3722d8` in an isolated review lane, with the plan committed and byte-identical to the
lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author`
CONFORMED (exit 0) before revision; after revision `--phase review-finalize` reports only the single
`IPD-Q501` for the blocking OQ-03 this round raised, which is the gate working rather than a structural
defect. This is Order 03 of `a5wdne`, whose orchestrator review and whose siblings `li44r9` and `nmlx47` I
have reviewed in earlier turns; I re-measured everything rather than importing conclusions.

THE EXPERIMENT IS THE RIGHT ONE, AND ITS FRAMING IS THE BEST THING IN THIS SET. Two sentences in the Goal
carry the whole argument and both are correct: "a seam extracted from two instances is fitted to those two
instances; the third is where an over-fitted abstraction reveals itself", and the declaration that "the
descriptor is insufficient, here is exactly how" is an ACCEPTABLE outcome. That second clause is what makes
this an experiment rather than a demo, and it is rare enough in this corpus to be worth naming. OQ-01's
resolution (a scripted host, not a vendor CLI) is also right and is properly evidenced.

MOST OF THE FACTUAL CLAIMS VERIFY. `HostLabels` is at `runner_shared.py:9425` with exactly 8 fields and an
empty `_field_defaults`, both instances constructed and bound (F-1, though the cited line was `:8530`,
stale by ~900). F-3's `options` asymmetry reproduces almost exactly:

```text
oc  options literal keys: 19    agy: 17
shared: 11 (incl. the ** spread marker, so 10 real keys)
oc-only:  7 ['agent','auto','launch_profile','no_audit','opencode','validate','variant']
agy-only: 6 ['agy_executable','dangerously_skip_permissions','effort','new_session','no_verify','timeout']
```

F-4 verifies in both consumers and turns out to be WORSE than stated, in a way that changes E-02's shape:
the two do not agree on the mechanism. `run_analytics_sources.py:206-207` takes `Path(raw).name` and looks
it up in `DRIVER_GENERATIONS`; `run_viewer.py:865-871` does substring matching (`if "oc_runipd" in
driver_path`) with a `Path(driver_path).stem` fallback. "Re-point both consumers" is therefore two different
edits. F-6 verifies (`host_launchers.py:17` "No live models are launched in tests (doubles only)";
`host_runner.run_worker_process` takes an injectable `runner`), with one limit worth recording: `host_runner`
is a different subsystem from the IPD driver, so it is a precedent for the METHOD and not an existing seam.
F-5's line figures are stale but directionally fine (measured 9708 / 5887 against the claimed 9588 / 5784).

**THE BLOCKER IS THAT THE FENCE MAKES THE PLAN UNEXECUTABLE, AND THE GAP IS FIVE FILES WIDE.** OQ-02 is
`Blocking: yes`, `Status: resolved` by the maintainer, and it commits this plan to four things: a host-id
field on `HostLabels`, both analytics consumers reading the id, a documented fallback so pre-cutover records
still attribute, and a test pinning both directions. Carrying those requires `run_analytics_sources.py`,
`run_viewer.py`, BOTH runners (the identity is written as `str(Path(__file__).resolve())` at
`oc_runipd.py:3641-3643` and `agy_runipd.py:2349-2351`) and `host_cmd.py` (whose `DEFAULT_HOSTS` at `:37` is
literally `("opencode", "antigravity")`, so a third host is invisible to `aw host capabilities` without it).
The plan declared `runner_shared.py`, one new test file and the research directory, while its own gate says
"commit only the declared `Scope-Paths`". This is the SAME defect the parent's review raised as PR-002 and
it was never fixed in the child.

**AND THE SEAM IS NARROWER THAN THE PLAN ASSUMES, WHICH IS THE MEASUREMENT E-01 SHOULD HAVE STARTED FROM.**
`HostLabels` models eight strings and one flag. It models none of the three things a host needs to run a
turn:

```text
ARGV   oc : [opencode, "run"] + --dir/--session/--model         (oc_runipd.py:5648)
       agy: [agy_bin, "-p", prompt, "--output-format",
             "stream-json", "--print-timeout", ...]              (agy_runipd.py:2730)
SPAWN  run_opencode (13 params) vs run_agy_turn (12, different set); each called by name
       from its own execute_item
OPTIONS 13 host-only keys across the two initialize_run literals
```

And the structural one, which I think is the most likely first wall: a `HostLabels` instance is bound by
call sites that live INSIDE a runner module, nine of them per host (measured: 9 `HOST_LABELS` references in
each). A host that is "only a descriptor" has nowhere to put those nine bindings. So "add a descriptor plus
a thin entry point" understates the work, and a gap list is the PREDICTED outcome rather than the fallback.
I rewrote the plan so that prediction is explicit and the result can be compared against it, because the
alternative is an executor who hits the first wall and cannot tell whether they made a mistake.

TWO PIECES OF GOOD NEWS THE PLAN UNDERSELLS, both worth stating because they remove work rather than adding
it. FIRST, spec `25kzda` is ALREADY N-host: assurance A4 is "host asymmetry", there is a mandatory
"Per-host capability descriptor" section whose text says "`oc` may support a capability that `agy` does not,
or vice versa; the descriptor controls the decision for the current installation", and each action packet
declares `required_host_capabilities`. The spec-sync section's fear that the spec "is written for two hosts"
is therefore mostly unfounded, and E-03 should not go hunting for an amendment it probably does not need.
SECOND, `host_sandbox_profile.detect_host_capabilities` is host-NAME driven with a single hardcoded
`opencode` branch (`:838`), so an unknown third host already reports fail-closed capabilities rather than
crashing; making it legible to `aw host capabilities` is a one-tuple edit plus honest probes.

V-02's evidence is also more readily available than the plan implies. The corpus holds 181 run records
across four historical driver basenames (`oc_runipd.py` 160, `runipd.py` 13, `agy_runipd.py` 5,
`ipdrunner.py` 2), and all four are already in `DRIVER_GENERATIONS`, so the pre-cutover half can be proven
against real recorded data rather than a synthesized fixture.

TWO SMALLER THINGS THAT WOULD HAVE MISDIRECTED AN EXECUTOR. The `## Proposed changes` list is off by one
against the checklist from step 2 onward: five steps for six E-items, with E-02 mapped onto E-03's work, the
gap classification labelled E-03, the research record E-04 and the guard E-05. Following the summary would
have performed the wrong item at every step after the first, and the Deferred section inherited the same
off-by-one. And E-04's classification vocabulary had three classes where four are needed: a gap caused by one
of the five still-forked large functions is an UNFINISHED MIGRATION, not a design failure, and filing it
under "structural limit" would condemn a design that is actually fine. Given the identity write sits inside
the forked `initialize_run`, that fourth class is where I expect at least two gaps to land.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | G. executability; A. correctness | OQ-02's four commitments; `run_analytics_sources.py:183-207`; `run_viewer.py:865-871`; `oc_runipd.py:3641-3643`; `agy_runipd.py:2349-2351`; `host_cmd.py:37`; `initialize_run` measured 446 oc / 353 agy raw lines | **THE FENCE EXCLUDES FIVE FILES THE MAINTAINER'S OWN RESOLVED RULING COMMITS E-02 TO EDITING, AND ONE PAIR IS INSIDE THE FORKED `initialize_run` THIS SET DELIBERATELY LEAVES ALONE.** The plan declared three paths and its gate says commit only those. The identity write is per-host and cannot be changed once, so E-02 is unexecutable as fenced AND arguably crosses the Set's own boundary. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | OPEN | Fence widened to eight paths and E-02 now names every write site with an explicit prohibition on lifting `initialize_run`. The SCOPE question (may this Set touch the forked functions at all?) is ESCALATED as OQ-03 (`Blocking: yes`, `Finding: PR-001`) with three priced options, because it is a Set-boundary call the maintainer drew. |
| PR-002 | HIGH | IN-SCOPE | C. architecture; G. executability | `runner_shared.py:9425-9481` (8 fields, no argv/spawn/options); `oc_runipd.py:5648` vs `agy_runipd.py:2730`; `run_opencode` vs `run_agy_turn` signatures; 9 `HOST_LABELS` references per runner | **`HostLabels` MODELS NONE OF THE THREE THINGS A HOST NEEDS TO RUN A TURN, AND ITS BINDING SITES LIVE INSIDE A RUNNER MODULE.** The plan's "descriptor plus a thin entry point" therefore understates the work materially: no argv contract, no spawn seam, 13 host-only `options` keys, and nowhere for a module-less host to bind its nine label sites. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A measured table added to the Goal marking each row modelled / not-modelled, with the binding-site problem named as the likely FIRST wall; E-01 now starts from that table and must extend it; E-03 predicts three specific walls so the result is comparable against a prediction; the Scope statement now says the gap list is the EXPECTED outcome. Recorded as F-8 and F-9. |
| PR-003 | HIGH | IN-SCOPE | A. correctness (an executor would perform the wrong step) | the `## Proposed changes` list vs the E-checklist; the Deferred section's "E-02 finds ... a finding for E-03" | **THE ORDERED SUMMARY IS OFF BY ONE FROM STEP 2 ONWARD:** five steps for six items, E-02 mapped to E-03's work, and every later item mislabelled. The Deferred section inherits the same error. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | List renumbered to six steps matching the six E-items, with the correction flagged in place; the Deferred cross-references corrected to E-03/E-04. Recorded as F-12/F-13. |
| PR-004 | HIGH | UNDER-SCOPE | D. anti-regression (a guard with no deliverable on the likely path) | E-06 as authored assumed a working third host; `tests/test_rununify_lift.py`'s two-directional precedent | **E-06 HAD NO DELIVERABLE ON THE OUTCOME THE PLAN ITSELF CALLS ACCEPTABLE.** If E-03 finds the seam insufficient, the authored E-06 ("assert the third host needs no runner module") is unsatisfiable, and the natural response is to weaken or drop it, losing the guard that stops the next integrator rediscovering the same wall. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 now has an explicit second mode: pin the measured LIMIT in the inverse direction, naming each blocking gap with its citation, following `test_rununify_lift.py`'s precedent, and fail loudly when a gap is closed. V-06 requires the guard be shown red either way. |
| PR-005 | MEDIUM | IN-SCOPE | A. correctness (two consumers, two mechanisms) | `run_analytics_sources.py:206-207` (basename -> `DRIVER_GENERATIONS`); `run_viewer.py:865-871` (substring + `stem` fallback) | **F-4 SAYS "BASENAME" FOR BOTH CONSUMERS AND ONLY ONE USES A BASENAME.** `run_viewer` substring-matches `"oc_runipd" in driver_path`. An executor treating them as one pattern would leave `run_viewer` attributing a runner-less host by `Path(...).stem` of whatever the id happens to be. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-4 rewritten with both mechanisms quoted; E-02 states they are two different edits; V-02 requires both exercised SEPARATELY and refuses evidence from one as covering the other. |
| PR-006 | MEDIUM | IN-SCOPE | G. executability (an incomplete classification vocabulary) | E-04's three classes; the identity write inside the forked `initialize_run` | **THE MISSING FOURTH CLASS IS THE ONE MOST LIKELY TO BE NEEDED.** A gap caused by one of the five still-forked large functions is an unfinished migration, not a design flaw, and filing it as "structural limit" would recommend redesigning a seam that is fine. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Class (d) BLOCKED ON THE REMAINING FORK added to E-04 with the reason the distinction matters; V-04 fails a class-(c) verdict on a class-(d) gap; the review's prediction of which gaps land where is recorded. Recorded as F-10. |
| PR-007 | MEDIUM | OVER-SCOPE | F. KISS (work the plan feared that it does not need) | `25kzda` A4 "host asymmetry"; its "Per-host capability descriptor" section; `required_host_capabilities` per action packet; `host_sandbox_profile.py:838` | **THE SPEC IS ALREADY N-HOST, so the spec-sync section's premise is wrong in the reassuring direction.** It anticipated finding a two-host assumption and filing an amendment. The spec explicitly contemplates hosts differing, and the capability prober is host-name driven with one hardcoded branch, so a third host is already fail-closed legible. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section rewritten with the three spec citations and an instruction NOT to hunt for an amendment on the assumption one must exist; `xdgorn` correctly re-scoped as a FLAG-asymmetry documentation gap that is its own item's to close. Recorded as F-11 and a conventions bullet. |
| PR-008 | MEDIUM | UNDER-SCOPE | E. testing (an unstated baseline and unproven surfaces) | measured `7975 passed, 3 skipped, 2 xfailed`; corpus of 181 run records across 4 basenames; `host_cmd.DEFAULT_HOSTS` | The required-tests section said "bare and green" with no figure, named no invocation form, did not require the pre-cutover evidence come from the REAL corpus, and never required the third host be shown in `aw host capabilities` despite the plan's own convention note demanding legibility to it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Baseline measured and written in with the invocation form and a NO-NEW-failures gate; both consumers required separately; pre-cutover evidence required from the corpus with the four basenames and their counts named; `aw host capabilities` output added as a required artifact. |
| PR-009 | MEDIUM | UNDER-SCOPE | G. executability (missing execution-contract elements) | the authored gate had approval, OQ-02, worktree, path-scoped-commit and never-push only | The contract omitted the two shortcuts that would produce a falsely-successful result (writing a third runner module; lifting `initialize_run` to change the identity once), the declare-and-justify scope wording, the shared-checkout re-verification step, the suite-baseline honesty rule, and the conditional finalize ownership. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | All added. The two prohibitions are stated with their reasons, since each would answer the plan's question NO while appearing to answer it YES; fence in declare-and-justify form per the 2026-09-01 ruling, with a legitimate stop for absent `nmlx47` symbols or a concurrent-edit conflict. |
| PR-010 | LOW | IN-SCOPE | G. traceability; A. correctness (stale citations) | no `- From-Backlog:` while `a5wdne`/`li44r9` carry `dstnso`; `HostLabels` at `:9425` not `:8530`; `oc_runipd.py` 9708 lines not 9588, `agy_runipd.py` 5887 not 5784 | The graduation link was missing, so this child's provenance was invisible to `aw check` and the close-legitimacy predicate, and three line figures were stale by 100 to 900 lines including the `HostLabels` anchor an executor navigates to first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- From-Backlog: dstnso` added; all figures re-measured in place with the authored value shown beside the measured one. Recorded as F-14 and in F-1/F-5. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001 has two halves: a fence that is too narrow, and a Set boundary the fix may cross. Fix both, or escalate? | FIX THE FENCE MYSELF (it is a declaration, and the files are measurable) and ESCALATE ONLY the boundary question as OQ-03. | (a) Escalate both, rejected: which files E-02 touches is a measurement, not a judgement, and asking the maintainer to enumerate them would waste a round trip on something an AST walk answers. (b) Fix both by declaring the runners and calling the boundary question settled, rejected: the Set defers the five large functions explicitly and its orchestrator has an open OQ-01 about their fate, so quietly authorizing an edit inside two of them would decide a question the maintainer reserved. | the five write/read sites measured; `initialize_run` measured at 446/353 raw lines and named in the Set's own deferral; `a5wdne` OQ-01 still open | yes |
| D-2 | The plan expects a working third host; I measured that it almost certainly cannot get one. Re-scope it, or let the experiment discover that? | RE-SCOPE THE EXPECTATION, not the work: keep every E-item, state the gap list as PREDICTED, and record the three specific walls so the result is comparable against a prediction. | (a) Leave the optimistic framing and let E-03 find out, rejected: an executor hitting the first wall cannot tell whether the seam is inadequate or they are doing it wrong, and the cheapest failure mode is that they "fix" it by writing a runner module. (b) Cut E-03 to an analysis-only item, rejected and this is the important rejection: that is exactly how `rununify` 07-11 stalled (all five re-scoped at review into analysis, all five recording NO SPLIT WAS PERFORMED), and the attempt is what produces the evidence. | `HostLabels` field list; the two argv constructions; the two spawn signatures; 9 binding sites per host; the `rununify` 07-11 precedent recorded in this Set's own orchestrator | yes |
| D-3 | E-06 is unsatisfiable if the seam turns out insufficient. Drop it, or give it a second mode? | GIVE IT A SECOND MODE: pin the measured LIMIT in the inverse direction, naming each gap, failing when a gap is closed. | (a) Make E-06 conditional on E-03 succeeding, rejected: that leaves the likely path with no durable artifact and invites the next integrator to rediscover the same wall. (b) Drop E-06 if gaps remain, rejected outright: `tests/test_rununify_lift.py`'s own docstring records why a one-directional suite is dangerous, and an unpinned exclusion is how a deliberate boundary gets "finished" by someone reading a count. | `tests/test_rununify_lift.py` two-directional precedent and its stated reason | yes |
| D-4 | The spec-sync section fears a two-host spec. Verify or leave the caution? | VERIFY AND CORRECT IT: the spec is N-host, and say so with citations. | (a) Leave the cautious wording, rejected: it would send E-03 looking for an amendment that is unlikely to exist, and a spec amendment is the highest-leverage change a run can make, so a speculative one is a real risk. (b) Delete the section as N/A, rejected: if a genuine two-host assumption does exist, the instruction to record it rather than edit the shipped contract is the right one and must survive. | `25kzda` A4; the per-host capability descriptor section; `required_host_capabilities`; `host_sandbox_profile.py:838` | yes |
| D-5 | Verdict and readiness with one OPEN BLOCKER? | `REVIEWED - OPEN QUESTIONS`, readiness `no-go`, `Status: reviewed`. | (a) `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval`, rejected: PR-001 is left OPEN at BLOCKER, which the readiness table names a genuine not-ready condition; the plan cannot execute E-02 until the boundary question is answered. (b) `REJECT - NEEDS REPLAN`, rejected: the experiment's design is sound and is the most valuable item in this Set; the blocker is a declaration plus a scope ruling, both bounded. | workflow verdict/readiness tables; PR-001 `Decision: OPEN`; `aw ipd lint` refusing on OQ-03 by design | yes |

### Escalation of the irreversible decisions

None of this round's five decisions is judged `Reversible: no`. Every one is undone by editing this plan
before it executes: nothing here publishes an interface, migrates data, deletes anything, or produces a
released artifact. The one decision that could become irreversible if wrong is D-1's escalation route, and
it fails in the safe direction: leaving OQ-03 blocking means the plan cannot execute until a human answers,
so a wrong call costs one round trip rather than an unauthorized edit inside a function the Set deferred.
Stated explicitly rather than left blank.

### Honest limits of this review

- I did NOT attempt the third host. Every claim about what the seam cannot express is derived from READING
  the argv construction, the spawn signatures, the `options` literals and the binding sites, plus counting
  them. That is strong evidence for "the descriptor does not model these", and it is NOT proof that a clever
  entry point could not work around them. E-03 remains the real test, which is why I re-scoped the
  EXPECTATION rather than pre-empting the result.
- My "three predicted walls" are a prediction and are labelled as one in the plan. If E-03 clears one, that
  is a genuine and interesting finding against this review, and I wrote V-03 to require that it be reported.
- I did not verify that a scripted host can satisfy `25kzda`'s `required_host_capabilities` for any real
  action packet. It plausibly cannot satisfy the mutate action's requirements, which would make "drive one
  real IPD execution" harder than E-03 assumes for reasons unrelated to `HostLabels`. I have not measured
  it and did not raise it as a finding; E-01's contract enumeration should surface it.
- The `sha256` companion field beside `driver.path` is flagged in E-02 as needing an answer, but I did not
  trace who READS it. If nobody does, the answer is trivial; if a consumer does, that consumer is a sixth
  file. I state the question rather than the answer.
- This plan declares `Item-Dependencies: executed:nmlx47`, and `nmlx47` is `reviewed`/`go-pending-approval`
  and unexecuted, so this plan cannot run yet regardless of its own readiness. Note also that `nmlx47`'s two
  blocking questions were resolved by a different agent after my review of it; I did not re-examine that
  resolution, and its E-02 scoping decision could change what symbols exist when this plan runs.
