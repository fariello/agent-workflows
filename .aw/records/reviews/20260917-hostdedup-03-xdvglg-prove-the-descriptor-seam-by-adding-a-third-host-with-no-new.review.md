# Review findings: plan xdvglg

- Subject-Id: xdvglg
- Subject-Type: ipd
- Reviewed-At: 2026-09-18
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

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

## Round 2

Reviewed at HEAD `a01c82ba`. The plan on disk is byte-identical to the lane input (`diff -q` clean), and
the last commit touching it is round 1's own `587b5823 plan-review: harden xdvglg (revisions applied)`, so
nothing has changed under it.

ROUND 2 IS AN AUDIT, NOT A SECOND OPINION, and the reason decides what is worth reporting. Round 1 left this
plan `REVIEWED - OPEN QUESTIONS` / `no-go` on one BLOCKER (PR-001) escalated as blocking OQ-03, awaiting a
maintainer Set-boundary ruling. Two gates are correctly holding it closed and I verified both rather than
assuming them: `aw ipd lint --phase author` refuses with `IPD-Q501 (line 298): OQ-03: BLOCKING question is
still 'open'`, and `review_findings.subject_gating_blocks(repo, "xdvglg")` returns one
`GatingBlock(finding_id='PR-001', severity='blocker', decision='open')`. So the plan cannot execute, and the
useful work this round is (a) checking whether the maintainer answered OQ-03, (b) re-deriving round 1's
measurements to see whether any were wrong or have drifted, and (c) finding what round 1 missed.

OQ-03 IS STILL UNANSWERED. No commit since round 1 touches the plan or the question.

I RE-DERIVED EVERY LOAD-BEARING MEASUREMENT ROUND 1 MADE, and they hold. This matters because round 1's
revisions inserted a lot of measured detail into the plan, and a wrong number there would mislead an
executor:

```text
HostLabels          : 8 fields, _field_defaults == {}            VERIFIED (fields listed below)
options split       : 10 shared / 7 oc-only / 6 agy-only = 13    VERIFIED, all 13 key names exact
binding sites       : 9 HOST_LABELS references per runner        VERIFIED (9 and 9)
identity writes     : oc_runipd.py:3642, agy_runipd.py:2350      VERIFIED (`"path": str(Path(__file__).resolve())`)
initialize_run size : 446 oc / 353 agy raw lines                 VERIFIED exactly
file sizes          : oc 9708, agy 5887                          VERIFIED exactly
argv divergence     : oc_runipd.py:5648 vs agy_runipd.py:2730    VERIFIED at the cited lines, zero overlap
two consumers differ: basename lookup vs substring + stem        VERIFIED (`run_analytics_sources.py:206-207`, `run_viewer.py:865-871`)
DEFAULT_HOSTS       : ("opencode", "antigravity")                VERIFIED (`host_cmd.py:37`)
capability prober   : single hardcoded `opencode` branch         VERIFIED (`host_sandbox_profile.py:838`)
spec 25kzda N-host  : A4 "host asymmetry" + descriptor + packets VERIFIED (`:120`, `:846`, `:865`)
doubles precedent   : "No live models are launched in tests"     VERIFIED (`host_launchers.py:17`)
From-Backlog dstnso : present, matching all three siblings       VERIFIED
```

Fields, for the record: `command`, `review_command`, `argv_tokens`, `argv_subcommands`, `product`,
`report_title`, `shell_tool`, `emits_launch_identity`.

THREE THINGS ROUND 1 GOT WRONG OR MISSED, all of them in the plan text it wrote, and one is a genuine
executability defect of the same class round 1 itself raised as PR-001.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | G. executability; A. correctness | `oc_runipd.py:3642`; `agy_runipd.py:2350`; `initialize_run` measured 446 oc / 353 agy raw lines; `a5wdne:237-258` (the Set's own OQ-01, still open); OQ-02's four commitments | **CARRIED FORWARD FROM ROUND 1, UNCHANGED AND STILL OPEN: may this Set edit the identity write inside the forked `initialize_run` at all?** Restated here DELIBERATELY and not by oversight. The typed gate reads only the CURRENT round (`ReviewDocument.current_findings`, documented at `check_engine.py:3161-3162`), so a round 1 BLOCKER that round 2 does not restate silently stops gating: measured, `subject_gating_blocks` returned round 1's PR-001 before this round existed and returned `()` after it, purely because the round advanced. Nothing about the finding was resolved. Round 2 re-derived every fact it rests on and all of them hold (both identity writes present at the cited lines, `initialize_run` still 446/353, the Set's OQ-01 about the five functions still `Status: open`), and D-201 records why I did NOT resolve it from the maintainer's 2026-09-16 de-duplication directive: that directive was given to the `rununify` Set about SPLITTING those functions, while this question asks whether a Set that explicitly EXCLUDES them may make a narrow edit inside one. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | OPEN | UNCHANGED: still escalated as OQ-03 (`Blocking: yes`, `- Finding: PR-001`), readiness stays `no-go`, and `aw ipd lint` continues to refuse with `IPD-Q501`. Round 2 made option (a) MORE executable (the ninth file is now fenced and the characterization re-base is specified) without deciding the boundary question, which remains the maintainer's. |
| PR-101 | HIGH | UNDER-SCOPE | G. executability; E. testing | `tests/test_rununify_initialize_run_characterization.py:230-233`, `:248-252`, `:292`; `.aw/records/plans/pending/...xdvglg...:7` | **A NINTH FILE IS AFFECTED AND UNDECLARED, AND IT PINS EXACTLY WHAT E-02 MUST CHANGE.** Round 1 widened the fence from 3 to 8 paths for the OQ-02 identity work but missed the TEST that characterizes the identity. `tests/test_rununify_initialize_run_characterization.py` asserts, against BOTH hosts, that `Path(state["driver"]["path"]).name == DRIVER_IDENTITY[name]["basename"]` (`:230-233`, whose docstring calls it "The load-bearing assertion"), that `Path(state["driver"]["path"]) == module_file` AND `state["driver"]["sha256"] == sha256_file(module_file)` (`:248-252`), and it re-derives the basename at `:292`. Measured green now (`35 passed`). E-02 changes what that field means, so these assertions must be RE-BASED deliberately under the maintainer's 2026-09-16 "re-base deliberately, never weaken silently" rule; undeclared, an executor either edits an unfenced file or reports a spurious regression. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | File added to `Scope-Paths` (now nine paths). E-02 now names the three assertion sites, instructs a deliberate re-base rather than a weakening, and cites the maintainer's rule; V-02 requires the re-based test shown green AND requires stating what each assertion now asserts. |
| PR-102 | HIGH | IN-SCOPE | A. correctness (evidence a lane cannot obtain) | `.aw/.gitignore:14` (`records/runs/`); measured `.aw/records/runs` does not exist in this lane; plan `:89`, `:113`, `:232-233`, `:343-347` | **ROUND 1 MANDATED PRE-CUTOVER EVIDENCE FROM A CORPUS THAT IS GITIGNORED AND ABSENT FROM EVERY LANE.** Round 1 measured "181 run records across four historical driver basenames" and wrote it into E-02, E-06, the required-tests section and V-02, instructing that the evidence "must be used rather than synthesized". But `.aw/records/runs/` is gitignored (`.aw/.gitignore:14`, "box-local, ephemeral working material; never committed"), and the directory does not exist in this checkout at all. So round 1 measured the maintainer's local state and then required a lane executor to reproduce it, which is unsatisfiable exactly as its own PR-001 was. THE FIX IS IN-TREE: `tests/test_run_analytics_sources.py:141-155` already holds real pre-cutover shapes for three generations (`oc_runipd.py`, `runipd.py`, `ipdrunner.py`) plus `agy_runipd.py` at `:449`, tracked and lane-reachable. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Every "use the real corpus" instruction re-pointed at the tracked fixtures with their line cites, and the 181-record figure re-labelled as a maintainer-local observation that an executor is NOT required to reproduce. The requirement that the evidence be REAL rather than synthesized is preserved, which was round 1's correct intent; only the unreachable source changed. |
| PR-103 | MEDIUM | IN-SCOPE | G. executability (a stale anchor an executor navigates to first) | measured `class HostLabels` at `runner_shared.py:9509`; plan cites `:9425-9481` in the Goal table and `:9425` in F-1 | **ROUND 1 CORRECTED THIS ANCHOR AND IT HAS ALREADY DRIFTED AGAIN, BY 84 LINES.** Round 1's own PR-010 fixed `:8530` to `:9425`; `runner_shared.py` has since grown to 10178 lines and the class is now at `:9509`. This is the same defect class round 1 raised, recurring for the same reason: a line number in the most-edited file in the repo is a perishable citation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Anchors updated to `:9509`, and the citation form changed to name the SYMBOL as authoritative with the line as a hint, so the next drift is not a defect. The same treatment applied to the two identity-write cites (now `:3642` / `:2350`). |
| PR-104 | LOW | IN-SCOPE | E. testing (a baseline that invites a false regression verdict) | measured `7993 passed, 3 skipped, 2 xfailed` with `env -u AW_EXECUTION_ROLE`; plan records `7975 passed, 3 skipped, 2 xfailed` | The suite baseline round 1 measured has drifted by 18 passing tests as the suite grew. Round 1 correctly gated on NO NEW failures rather than an absolute count, so this is not a trap, but the stale figure is the number an executor will compare against and a difference of 18 invites a hunt for a nonexistent cause. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both baselines now recorded with their HEADs, and the plan states explicitly that the pass TOTAL drifts with suite growth while the NO-NEW-FAILURES gate is the invariant. |
| PR-105 | LOW | IN-SCOPE | G. executability (an unanswered question round 1 left open) | `tests/test_rununify_initialize_run_characterization.py:240-252` is the ONLY reader of `driver.sha256` (measured across `agent_workflows/` and `tests/`) | Round 1 flagged in E-02 that a runner-less host has no module to digest and asked what it records in `sha256`, and listed "I did not trace who READS it" as an honest limit, noting that a consumer would make it "a sixth file". I traced it: exactly one reader exists, the characterization test above, and no product code reads it. So the question round 1 left open is now answerable, and its answer is the same file as PR-101. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now records that no PRODUCT consumer reads `driver.sha256` and that its only reader is the characterization test, so the field's fate is a test re-base decision rather than a new consumer migration. Round 1's honest limit is closed in place. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-201 | The maintainer's 2026-09-16 directive ("at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code") plus the resolved OQ-03 of `orziju` ("ROUTE (A) ... So DO THE SPLIT") arguably already authorize the narrow `initialize_run` identity edit that this plan's OQ-03 asks about. Should I resolve OQ-03 from that evidence and clear the BLOCKER? | NO. Leave OQ-03 open and the readiness `no-go`; record the directive IN the question so the maintainer decides with it in view. | (a) Resolve OQ-03 as "authorized, proceed with option (a)": rejected, the directive was given to the `rununify` Set about SPLITTING the five functions, and this plan's question is whether a DIFFERENT Set (`hostdedup`, which explicitly excludes those five) may make a narrow edit inside one of them. Those are different questions and the second is a Set-boundary call the maintainer drew. (b) Escalate a second blocking question: rejected as redundant, OQ-03 already blocks. | The directive is quoted in `.aw/records/plans/executed/20260915-rununify-09-orziju-...ipd.md:280-285` and scoped to that Set; the `hostdedup` orchestrator's own OQ-01 (`a5wdne:237-258`) records that the five functions' fate is STILL an open maintainer question with three routes, and is `Blocking: no` only because that Set "proceeds on the other 29 symbols either way". So the authority for a `hostdedup` edit is genuinely unsettled. | yes |
| D-202 | Round 1 required pre-cutover attribution evidence from `.aw/records/runs/`, which is gitignored and absent from every lane. Substitute a source, or drop the requirement? | Substitute the tracked fixtures in `tests/test_run_analytics_sources.py`, keeping the requirement that the evidence be real. | (a) Drop the pre-cutover requirement: rejected, it is commitment (3) of the maintainer's resolved OQ-02 and the part round 1 rightly called most likely to be missed. (b) Let the executor synthesize a record: rejected, round 1 explicitly forbade synthesis and was right, since a hand-built shape can encode the very assumption under test. (c) Un-ignore the runs directory: rejected, it is deliberately box-local per `.aw/.gitignore:9-14`. | `.aw/.gitignore:14`; `.aw/records/runs` measured absent; `tests/test_run_analytics_sources.py:141-155` and `:449` hold real shapes for all four generations, and `DRIVER_GENERATIONS` has exactly those four keys. | yes |
| D-203 | PR-101's characterization test asserts the CURRENT `__file__`-derived identity. Is changing it a weakening of a guard? | No: it is a deliberate RE-BASE, and the plan must say so explicitly and prove the assertion still catches what it was installed for. | (a) Treat the test as immovable and block E-02 on it: rejected, the maintainer ruled directly that "TESTS ARE NOT IMMOVABLE" and that a source-reading pin is "something to UPDATE DELIBERATELY as part of the work". (b) Leave it undeclared and let the executor decide: rejected, that is how an unfenced edit or a spurious regression report happens. | The re-base rule is quoted in `orziju:287-296` ("re-base it on the code's new location, record what it now asserts, and prove it still catches the regression it was installed for ... WHAT REMAINS FORBIDDEN is WEAKENING a guard silently"). The test is measured green (`35 passed`) so its current state is a real baseline. | yes |

### Round 2 honest limits

- I did NOT attempt the third host either, so round 1's central honest limit stands unchanged: every claim
  about what the seam cannot express is derived from reading and counting, and E-03 remains the real test.
- I did not re-examine round 1's nine FIXED findings for quality beyond re-deriving their measurements. I
  checked that what round 1 wrote into the plan is TRUE, not that it was the best possible revision.
- Round 1 listed as a limit that it had not verified whether a scripted host can satisfy `25kzda`'s
  `required_host_capabilities` for a real action packet. I did not measure that either, and it remains the
  most likely way E-03 gets blocked for a reason unrelated to `HostLabels`. E-01's enumeration should surface
  it; I am recording the non-measurement rather than letting the limit quietly disappear between rounds.
- `nmlx47` (this plan's declared dependency) is still `reviewed`/`go-pending-approval` and unexecuted, so
  this plan cannot run regardless of OQ-03. The runner handles that correctly by marking the item
  `dependency-blocked` at dispatch; it is not a defect and I raise it only so the maintainer knows OQ-03 is
  not the only thing standing between this plan and execution.

## Round 3

Reviewed at HEAD `7a28ed11` with the maintainer.

OQ-03 RESOLVED AND PR-001 DISCHARGED. Following the maintainer's direct instruction, `initialize_run` across `oc_runipd.py` and `agy_runipd.py` was unified into `runner_shared.initialize_run_core` in commit `7a28ed11`. The driver identity write (`state['driver']`) now sits centrally in `runner_shared.py` (line 10433), parameterized by caller, completely removing the fork conflict that motivated PR-001 and OQ-03. All blocking questions on plan `xdvglg` are resolved; all findings PR-001..PR-010 and PR-101..PR-105 are FIXED.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | G. executability; A. correctness | `runner_shared.py:10433-10436`; commit `7a28ed11` | **CARRIED FORWARD FROM ROUND 1/2: may this Set edit the identity write inside initialize_run?** Resolved by unifying initialize_run into runner_shared.py (commit `7a28ed11`). The driver identity write is now centralized in shared code and parameterized by caller. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved by commit `7a28ed11`. The identity write is now centralized in `runner_shared.initialize_run_core`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-301 | OQ-03 resolution and PR-001 disposition | Mark OQ-03 resolved and PR-001 FIXED in Round 3; promote readiness to `go-pending-approval` | Leave open | Maintainer direct instruction and implementation in commit `7a28ed11` unifying initialize_run into runner_shared.py | yes |
