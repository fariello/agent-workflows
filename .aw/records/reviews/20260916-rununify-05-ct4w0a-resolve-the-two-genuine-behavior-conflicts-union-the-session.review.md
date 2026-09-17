# Review findings: plan ct4w0a

- Subject-Id: ct4w0a
- Subject-Type: ipd
- Reviewed-At: 2026-09-16
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `f5fee59b`. Structural preflight `aw ipd lint --phase author` CONFORMED (exit 0) before
revision. No pre-review snapshot needed: the plan was committed and unmodified. This is the third
`rununify` child reviewed today and it is MATERIALLY BETTER FOUNDED than the two before it, which is
worth saying first because the finding count alone would misrepresent it.

EVERY CLAIM IN THIS PLAN'S FINDINGS TABLE REPRODUCES. I checked all five rather than sampling. F-1's
capability loss I confirmed by EXECUTION, not by reading: oc's reader returns `None` on an agy-shaped log
where agy's returns the id, so "oc wins" would genuinely break agy's session tracking. F-2's asymmetric
`ses_` preference is real and is exactly as described. F-3's missing baseline declaration is real. F-4's
gitignored corpus is real (627 logs present in a primary checkout, `records/runs/` ignored at
`.aw/.gitignore:14`). F-5 holds. Its two open questions were put to the maintainer and answered
per-symbol, its rationales are honest, and unlike its siblings it did not assert a measurement it had not
taken; it correctly deferred the census to execution time. The defects below are OMISSIONS, and two of
them are serious.

I PERFORMED E-01's CENSUS MYSELF, because a plan whose design rests on a measurement deferred to
execution can be reviewed properly only by taking that measurement. Across all 627 session logs:
`sessionID` appears 167,921 times in 593 files and EVERY value is `ses_`-prefixed; `conversation_id`
appears twice, in 2 files, both agy-produced, both flat AND nested under `result`; `sessionId`,
`session_id`, and the entire `init` nesting path appear ZERO times. Two consequences the plan did not
anticipate. First, oc's `ses_` PREFERENCE is unexercisable in the real corpus: zero logs carry both a
prefixed and an unprefixed value, which is the only shape where the preference decides anything. It is
still a TESTED contract (`tests/test_oc_runipd.py:866`) and must be kept, but the plan's justification
for keeping it ("a real oc behavior agy's version drops") claims observational grounding it does not
have. Second, and more dangerous, E-01's own deletion rule fires on most of the union: three of four keys
and one of two nesting paths are unobserved, and E-02 instructs the executor to "drop it and record the
deletion" unless a launcher documents the shape. Followed literally, an executor would NARROW a
wire-format reader on the basis that 627 logs did not happen to contain a shape, which is
absence-of-evidence reasoning, and would silently change oc's LIVE `_event_session_id`
(`oc_runipd.py:3763`), a second consumer of the same constant that the plan never mentions.

THE UNION IS NOT THE STRICT SUPERSET THE PLAN CLAIMS, and this is the finding I would most want the
author to see. The phrase "a superset harming neither host" appears in both the Scope line and OQ-01's
resolution. The two readers differ in RETURN DISCIPLINE as well as key coverage: agy returns the first
non-empty hit IMMEDIATELY, while oc scans the whole file and treats a non-`ses_` value only as a
fallback. So on a log carrying agy's `conversation_id` early and a `ses_` value later, agy returns
`conv-FIRST` today and the union returns `ses_LATER`. I executed both readers on exactly that log to
confirm. The shape occurs in 0 of 627 logs, so the risk is LATENT rather than live and the union is still
right, but the plan would have shipped a precedence change that nobody chose and no test pinned.

THE BLOCKING PROBLEM IS ELSEWHERE ENTIRELY, AND THE PLAN IS SILENT ON IT. Lifting `driver_begin` breaks
three existing guards. Each driver file has EXACTLY THREE `argv`/`cmd` subprocess sites (`driver_begin`,
`driver_finalize`, the agent `Popen`); `tests/test_nested_tty_noninteractive.py:172` asserts at least
three PER FILE, so removing one fails with "call sites vanished". `:218` asserts each driver's own
stdin-guarded count plus the shared count is at least three, and today that is exactly `2 + 1`. And
`tests/test_lane_tool_identity.py:486` asserts the LITERAL TEXT `env=pinned_child_env()` inside
`inspect.getsource(driver_begin)` for BOTH hosts, which no shared-definition-plus-wrapper arrangement can
provide; oc's own body carries a comment saying that literal is kept visible deliberately for this guard.
These are not incidental test churn. They encode two properties this repository has already paid for: a
nested `aw` that inherited a TTY wedged a finalize for 1 hour 49 minutes waiting on input nobody could
see, and the tooling pin exists because a lane-shadowed `agent_workflows/` was measured resolving to the
wrong copy. Re-counting a structural guard so it still refuses a real regression, rather than merely
turning green, is a design act. `818uru` faced the identical problem when `run_checked` became shared and
its answer (give the shared file its own count, add it to both sides, do NOT lower the threshold) is a
house precedent I could apply mechanically, but applying it to a SECOND symbol is a judgement about how
much per-file coverage is still enough. That is OQ-03, and it is why this plan is NO-GO.

ONE MORE ABSENCE WORTH THE PLAN's ATTENTION: agy's `conversation_id` key and its `result`/`init` nesting
have ZERO test coverage anywhere in the suite. `extract_session_id` is exercised only in
`tests/test_oc_runipd.py`, in two oc-shaped cases. So F-1's central hazard, that adopting oc alone
silently disables agy session resume, is currently BOTH true and undetectable by the suite. New coverage
for agy's wire format is the most durable thing this plan can deliver and it deserved to be a named
outcome rather than a side effect of an identity assertion.

WHAT I FIXED AND WHAT I LEFT. I recorded the census as a baseline E-01 must now confirm or contradict by
name; neutralized E-01's deletion clause for this symbol with the reason; stated the precedence change
and required a test pinning it; added the guard re-count as its own E-item with an injected-regression
requirement, because a green re-count that no longer refuses a removed `stdin=` has traded safety for a
passing suite; added the missing agy coverage as an explicit deliverable; noted agy's dead `fallback`
variable; removed the unfounded `executed:i3d6ml` dependency edge after closure-checking both symbols;
and fenced the five test files the change must touch. I did NOT choose how to re-count the guards,
because narrowing a TTY or tooling-pin guard should carry a human's signature rather than a reviewer's.

THE `extract_session_id` HALF IS SOUND AND UNBLOCKED. It is closure-clean (its only module dependency is
`_SESSION_ID_KEYS`, which moves with it), needs nothing from any other child, and its ruling is correct.
That separability is what makes OQ-03's option 3 viable.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-201 | BLOCKER | UNDER-SCOPE | D. anti-regression; B. security (TTY / tooling pin) | `tests/test_nested_tty_noninteractive.py:172`, `:218`; `tests/test_lane_tool_identity.py:486`; measured 3 `argv`/`cmd` sites per driver file | **LIFTING `driver_begin` BREAKS THREE SAFETY GUARDS AND THE PLAN NAMES NONE.** Two count `subprocess` launch sites per driver FILE and require at least three; each host has exactly three, so removing one fails. The third asserts the LITERAL `env=pinned_child_env()` inside each host's `driver_begin` source, which a shared definition cannot satisfy. They encode measured incidents (a 1h49m TTY wedge; lane-shadowed tooling resolution), so re-counting them is a design act, and the easy fix (lower the threshold) turns both TTY guards into decoration, which `818uru`'s docstring already refuses in writing. | C:Medium-High; U:Low; S:Medium-High; F:Medium; Overall:Medium-High | OPEN | Added as its own E-03 with an injected-regression requirement in V-03, so a re-count cannot pass by weakening. HOW to re-count is escalated as OQ-03 with four options, the `818uru` precedent, and a recommendation (re-base on the owner set; fallback: take only the session-reader half). |
| PR-202 | HIGH | IN-SCOPE | A. correctness | executed at review: agy returns `conv-FIRST`, oc/union returns `ses_LATER` on the same log | **THE UNION IS NOT "A STRICT SUPERSET HARMING NEITHER HOST"** (the phrase used in the Scope line and OQ-01). The readers differ in RETURN DISCIPLINE: agy returns the first hit immediately; oc scans the file and treats a non-`ses_` value as a fallback. On a log carrying agy's key early and a `ses_` value later, the union changes agy's answer. 0 of 627 logs carry that shape, so it is latent, but the plan asserts an equivalence that does not hold and would ship an unchosen precedence change. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | OQ-01's claim withdrawn with the executed counter-example; E-02 now requires the precedence change be STATED as a decision; Required tests item 3 and V-02 pin the answer with a test. |
| PR-203 | HIGH | UNDER-SCOPE | E. testing (an absent capability test) | `conversation_id` appears in NO test file; `extract_session_id` exercised only in `tests/test_oc_runipd.py` (2 oc-shaped cases) | **agy's WIRE FORMAT HAS ZERO TEST COVERAGE, so F-1's central hazard is both true and undetectable.** The plan's own headline risk (adopting oc alone silently disables agy session resume) cannot currently be caught by the suite in either direction. New coverage for agy's key and nesting is the most durable deliverable here and appeared only implicitly, as a by-product of E-05's identity assertions. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 makes it an explicit outcome; V-06(c) requires the new tests be shown FAILING against oc's reader, so they prove the capability rather than the union's existence. |
| PR-204 | MEDIUM | IN-SCOPE | A. correctness (a rule that fires wrongly) | census: `sessionId`, `session_id`, `init` nesting all ZERO in 627 logs; `oc_runipd.py:3763` reads the same constant | **E-01's DELETION CLAUSE, APPLIED TO THE REAL CENSUS, WOULD NARROW THE UNION ON ABSENCE-OF-EVIDENCE.** Three of four keys and one of two nesting paths are unobserved; E-02 says to drop such a branch unless a launcher documents it. That reasons from a sample that cannot prove absence, and `sessionId`/`session_id` are additionally read by oc's LIVE `_event_session_id`, a second consumer the plan never mentions. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02(b) now neutralizes the clause for this symbol with the reason stated; the second consumer is recorded in Project conventions; E-06 requires the retained unobserved branches to be TESTED, which is the honest price of keeping them. |
| PR-205 | MEDIUM | IN-SCOPE | A. measured claims are verified | census: all 167,921 `sessionID` values `ses_`-prefixed; ZERO logs carry both shapes | **oc's `ses_` PREFERENCE IS UNEXERCISABLE IN THE REAL CORPUS,** so F-2's "a real oc behavior agy's version drops" is true of the CODE and not of the DATA. The preference must still be preserved (it is pinned by `tests/test_oc_runipd.py:866`), but the plan's justification claims observational grounding it lacks, and E-01 was written to distinguish exactly that ("keep a capability that is real, not one that is merely coded") while E-02 pre-committed to preserving it regardless. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-7 records the measurement; E-02 now frames the preference as a TESTED CONTRACT rather than an observed behavior, which is the accurate reason to keep it. |
| PR-206 | MEDIUM | IN-SCOPE | G. dependencies and sequencing | closure check: `extract_session_id` -> `Path`/`json`/`_SESSION_ID_KEYS`; `driver_begin` -> `Path`/`subprocess`/`begin_baseline_env`/`pinned_child_env`/`pinned_module_argv` | **THE `executed:i3d6ml` DEPENDENCY IS UNFOUNDED for both symbols.** Nothing either one references is among child 03's 48, and `pinned_child_env`/`pinned_module_argv` are already shared objects reachable from both hosts. The plan waited on child 03 for nothing. (Same pattern found in child 04 earlier today.) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Edge removed (`Item-Dependencies: none`), freeing the plan to run first; the closure result recorded in F-12. |
| PR-207 | MEDIUM | UNDER-SCOPE | G. scope fence | `driver_begin` referenced by 7 test files; `extract_session_id` by `tests/test_oc_runipd.py` | **THE FENCE NAMES ONE NEW TEST FILE AND NO EXISTING ONE,** though three existing files MUST change (PR-201) and others exercise both symbols. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Five existing test files added to `Scope-Paths`; each named in Project conventions or Required tests with the assertion that constrains it. |
| PR-208 | LOW | IN-SCOPE | F. prevent silent failure (dead code) | `agy_runipd.py:2471` initializes `fallback`, `:2497` returns it; every assigning branch returns first | **agy's `extract_session_id` CARRIES A DEAD `fallback` VARIABLE** that can never be non-`None` at the return. Harmless today, and exactly the residue that makes a future reader believe agy has a fallback discipline it does not have, which is the misreading that produced PR-202's "strict superset" claim in the first place. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02(c) requires it deleted rather than carried forward; V-02 requires confirmation. |
| PR-209 | LOW | UNDER-SCOPE | E. testing (a contract pinned by tests, not a spec) | `tests/test_begin_dirty_gate_scope.py:301`-`:315` | **THE `begin_baseline_env` CONTRACT IS PINNED BY TESTS AND THE PLAN DOES NOT NAME THEM.** That file asserts the exact env dict per `isolated` value and `driver_begin`'s keyword-only parameter with a `False` default, so it is the closest thing to a spec for what the adoption must preserve; the spec-sync section correctly says no `.spec.md` governs it but then cites only a docstring. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named in Required tests item 6, fenced, and cited in the spec-sync section as the actual pin. |
| PR-210 | LOW | IN-SCOPE | E. achievable bar | measured `1 failed, 7308 passed, 3 skipped, 2 xfailed`; the failure passes in isolation | **THE SUITE BASELINE IS UNSTATED AND ONE FAILURE IS PRE-EXISTING** (`ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`, a load-dependent 30s subprocess timeout). "No new failure against the baseline at execution time" leaves the executor to rediscover it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-14 records the measurement; Required tests item 8 and V-06(d) name the flake and require the isolation re-run as disposing evidence. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | E-01 defers the log census to execution time. Review the plan without it, or take the measurement myself? | TAKE IT. Scan all 627 logs and record the result as a baseline E-01 must confirm or contradict by name. | (a) Review without it, rejected: the union's design depends on the census, so a review that skips it can only check internal consistency, and the two most consequential findings (PR-204, PR-205) are invisible without the numbers. (b) Sample a handful of logs, rejected: the decisive facts are ABSENCES (three keys at zero, zero mixed-preference files), and a sample cannot establish an absence even weakly. | 627 logs under `.aw/records/runs/*/sessions/*.jsonl` at HEAD `f5fee59b`; per-key and per-nesting counts recorded in the plan's Goal table | yes |
| D-2 | The census shows three keys and the `init` nesting at ZERO occurrences. Follow E-01's deletion clause, or retain them? | RETAIN ALL, and neutralize the deletion clause for this symbol explicitly. | (a) Delete the unobserved keys per E-01's own rule, rejected on two grounds: 627 logs cannot prove a wire format never emits a shape, and `sessionId`/`session_id` are read by oc's LIVE `_event_session_id`, so deleting them changes a path the plan never examined. (b) Retain silently, rejected: an unobserved untested branch rots, which is the legitimate worry E-01's clause was written to address. So retain AND test (E-06). | census counts; `oc_runipd.py:3763` `_event_session_id` reading the same `_SESSION_ID_KEYS` tuple; E-01's own "candidate for deletion" wording | no |
| D-3 | OQ-01 states the union is a strict superset harming neither host. Keep that, or contradict it? | CONTRADICT IT, with the executed counter-example, and require the precedence change be recorded as a decision. | (a) Keep the claim since the harmful shape occurs in 0 of 627 logs, rejected: "does not occur today" and "cannot harm either host" are different statements, and the plan asserts the second. (b) Reopen the union ruling itself, rejected as unnecessary: the union is still correct, only its justification was overstated. | executed both readers on a log with `conversation_id` early and a `ses_` value later: agy returns `conv-FIRST`, oc/union returns `ses_LATER`; 0 of 627 logs carry both | yes |
| D-4 | Should the `executed:i3d6ml` edge stay? | REMOVE it. | (a) Keep as harmless caution, rejected: a false edge makes a runnable plan wait and the runner re-checks edges at dispatch, so the cost is real. (b) Keep because `driver_begin` is complex, rejected: complexity is not a dependency, and the closure check names every symbol it actually needs. | closure check of both symbols against child 03's 48; `agy_runipd.pinned_child_env is oc_runipd.pinned_child_env` verified True | yes |
| D-5 | The three broken guards: pick a re-counting scheme myself (the `818uru` precedent is clear), or ask? | ASK. Raised as OQ-03, `Blocking: yes`, four options, the precedent, and a recommendation. | (a) Apply `818uru`'s own-plus-shared pattern myself, rejected: it is the likely answer but it WEAKENS the per-file guard (a driver could reach the threshold with fewer of its own sites), and deciding how much structural coverage per file is still enough is a safety judgement, not a mechanical one. (b) Lower the thresholds to 2, rejected outright: `818uru`'s docstring records that this "would have made this pass while silently accepting a future change that actually removed a `stdin=`". (c) Keep a per-host wrapper containing a real `subprocess.run` so all three guards pass untouched, rejected as duplication wearing a wrapper (recorded as option 4 for the maintainer). | `tests/test_nested_tty_noninteractive.py:172`,`:218` and its `818uru` docstring; `tests/test_lane_tool_identity.py:486`; the 1h49m TTY wedge and `af7i6p` lane-shadowing incidents the guards encode | yes |

### Deferred and open

- `PR-201` - `OPEN`:
  - Reason: The breakage is measured precisely, but HOW to re-count three shipped safety guards once a launcher is shared is a design judgement about how much structural coverage per file is still enough, and the wrong answer silently disarms a TTY guard.
  - Remediation Risk: Medium-High
  - Axis: security, complexity
  - Required decision or evidence: the maintainer's answer to OQ-03 (extend the `818uru` per-file pattern; re-base the guards on the owner set; take only the session-reader half now; or keep a per-host wrapper).
  - Consequence if unresolved: the `driver_begin` half cannot land, so an isolated agy turn keeps asking `aw ipd begin` to gate on the main tree's baseline when it will execute in a lane. The `extract_session_id` half is unaffected and could proceed alone.

### Escalation of the irreversible decision

D-2 is judged `Reversible: no`: it decides AGAINST deleting three keys and a nesting path from a
wire-format reader, and the opposite choice (deletion) is what cannot be cleanly undone, because once the
branches are gone the evidence that they were ever supported is a git archaeology exercise and any host
emitting that shape fails silently. Escalated per the workflow rather than merely recorded: it is raised
in the plan as F-8 with the census that justifies it, E-02(b) carries the instruction NOT to apply the
deletion clause, the second consumer (`_event_session_id`) is named in Project conventions so a future
editor of the constant sees it, and E-06 requires the retained branches to be tested so their retention
is enforced rather than trusted. The `Blocking: yes` OQ-03 puts the plan in front of the maintainer before
any of it executes.

### Honest limits of this review

- MY CENSUS PROVES PRESENCE, NOT ABSENCE. Three keys and the `init` path show zero occurrences in 627
  logs from ONE box's history. That is enough to refute "these are observed capabilities" and NOT enough
  to conclude a host never emits them, which is precisely why D-2 retains them. A different checkout with
  different run history could show otherwise.
- THE `conversation_id` EVIDENCE IS THIN IN ABSOLUTE TERMS: 2 events across 2 files. It is unambiguous
  (both agy-produced, both flat and nested) and it is sufficient to confirm F-1, but nobody should read
  it as characterizing agy's wire format broadly.
- I DID NOT RUN THE THREE GUARDS AGAINST AN ACTUAL LIFT. I reproduced their counting logic on today's
  source and computed what removing one site yields. That is strong for the two counting guards and for
  the literal-text guard, but an executor could find a fourth guard I did not enumerate; V-03 is written
  to surface that rather than assume my list is complete.
- I DID NOT DECIDE THE GUARD RE-COUNT (D-5), and my recommendation of option 2 is a recommendation. I
  also did not evaluate whether `818uru`'s own-plus-shared scheme has already weakened the guard more
  than intended, which is a question about a landed plan rather than about this one.

## Round 2

DISCHARGE ONLY. NO NEW REVIEW WAS PERFORMED. This round records that round 1's gating findings were
resolved by the maintainer's own directive, given on 2026-09-16 in an interactive session. Nothing in the
plan was re-reviewed here and no new finding was sought; appending a round is the mechanism
`plan-review.md` prescribes for this, since the gate reads only the current round. Round 1 is left exactly
as written, and its measurements remain the specification the execution must reproduce at execution HEAD.

THE DIRECTIVE, quoted: "at the end of the SET, there should be one code base shared by the two runners
that contains 100% of the otherwise redundant code that currently is duplicated between the two runners."

TWO SUPPORTING RULINGS the maintainer gave in the same session, because round 1's findings rested on
premises both of them contradict. FIRST, TESTS ARE NOT IMMOVABLE: asked directly whether the
source-reading guards prevent this work, the answer was no, and the maintainer pointed at this
repository's own precedent where such a guard was already re-based for shared code
(`tests/test_nested_tty_noninteractive.py:190-203`, whose docstring records the reasoning; all 41 tests in
that file and `tests/test_lane_tool_identity.py` pass at this HEAD, verified 2026-09-16). SECOND,
COORDINATED DE-DUPLICATION IS PERMITTED: many functions may be de-duplicated together before testing, so
a dependency that is still double-defined because a sibling has not landed is an ordering matter, not a
blocker. What remains forbidden is weakening a guard silently.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | BLOCKER | IN-SCOPE | round 1 finding, discharged by directive | this plan's resolved `OQ-03`; the maintainer's 2026-09-16 directive | Lifting the driver-launch function breaks three safety guards that count nested-launch sites per driver FILE and pin a literal env call. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The maintainer ruled 2026-09-16 that these guards are work, not blockers, and selected option 2: re-base them on the OWNER SET rather than on files. Evidence the maintainer cited: this repository ALREADY adapted this exact guard for shared code (`tests/test_nested_tty_noninteractive.py:190-203` counts the shared file toward both runners) and all 41 tests in that file plus `tests/test_lane_tool_identity.py` pass at this HEAD, verified 2026-09-16. Weakening remains forbidden: the injected-regression test must survive and the `env=pinned_child_env()` pin must be re-pointed at the shared function, not deleted. See the resolved OQ-03. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the maintainer's directive discharge round 1's gating findings, or do they need a fresh review pass? | It discharges them; record the discharge and leave round 1 untouched. | A further full review round on this plan, rejected on cost and on relevance: round 1 already measured the mechanics correctly and its findings were escalations of a SCOPE decision, which is the maintainer's to make and which they have now made. | The findings' own recorded remedy was a maintainer decision, and that decision is now recorded in this plan's resolved OQ-03 with its reasoning and its two supporting rulings. | yes |

HONEST LIMIT, stated because it bounds what this round proves: the discharge rests on the maintainer's
directive, NOT on an independent reviewer's re-examination of the plan's content. Round 1 is where that
assurance lives. Specifically NOT re-verified here: the closure and pin measurements round 1 recorded
(each plan's E-01 re-measures them at execution HEAD and is required to refuse on a stale list), and
whether the re-based guards preserve their properties (each plan's V-items require that evidence). This
round changes the DECISION column and nothing else.
