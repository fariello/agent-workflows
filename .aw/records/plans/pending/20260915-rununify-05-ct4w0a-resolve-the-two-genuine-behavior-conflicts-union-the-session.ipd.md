# IPD: Resolve the two genuine behavior conflicts, union the session id reader and adopt the isolated begin baseline

- Date: 2026-09-15
- Kind: child
- Concern: `extract_session_id` and `driver_begin` are the ONLY two shared runner symbols where the hosts genuinely disagree about behavior rather than about strings or style. A blind "oc wins" breaks Antigravity's session tracking outright, because oc's reader cannot see agy's wire format.
- Scope: Unify both through `runner_shared.py` using the maintainer's 2026-09-14 per-symbol rulings: UNION for `extract_session_id`, and ADOPT OC for `driver_begin` (agy gains the isolated-baseline declaration it silently lacks). CORRECTED AT REVIEW 2026-09-16: the union is NOT "a superset harming neither host" (F-6, it changes agy's answer on a log carrying both shapes), and lifting `driver_begin` BREAKS THREE EXISTING STRUCTURAL GUARDS that count subprocess launch sites per driver FILE (F-9), which is the reason its disposition is now OQ-03 and `Blocking: yes`.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_conflicts.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_nested_tty_noninteractive.py, tests/test_lane_tool_identity.py, tests/test_begin_dirty_gate_scope.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: rununify
- Order: 5
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: ct4w0a
- Approval: 2026-09-17, human ("approved"): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- From-Backlog: alw22r

## Workflow history
- 2026-09-17 approved (aw set, --by-human): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- 2026-09-16 reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION 2026-09-16: readiness set to `go-pending-approval` BY THE MAINTAINER, not by an agent and not by a review. The prior `no-go` was written by this plan's own 2026-09-16 review round while its blocking OQ-03 was genuinely open. The maintainer then answered that question directly in an interactive session on 2026-09-16 with a single Set-wide directive ('at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code that currently is duplicated between the two runners'), plus two supporting rulings that dissolved the premises the finding rested on: TESTS ARE NOT IMMOVABLE (a source-reading guard is re-based deliberately as part of the work, never weakened silently; the maintainer cited this repository's own precedent at `tests/test_nested_tty_noninteractive.py:190-203`, whose 41 related tests pass at this HEAD) and COORDINATED DE-DUPLICATION IS PERMITTED (many functions may be de-duplicated together before testing, so a still-double-defined dependency is an ordering matter rather than a blocker). Asked directly how the stale verdict should be cleared, the maintainer chose to attest it themselves rather than fund a further review round. THE ALTERNATIVE WAS PRICED AND REJECTED ON EVIDENCE: the 2026-09-16 round cost roughly 2.5 hours across nine items and produced 1,479 lines of review prose while clearing nothing, and the comparable 2026-09-13 round cost $106.07 and raised four NEW blocking questions, so a further round was not expected to yield a clean sheet. NO AGENT WROTE THIS VALUE ON ITS OWN AUTHORITY. HONEST LIMIT: no independent reviewer re-examined this plan's contents; that assurance lives in the 2026-09-16 round 1 record, not in this attestation. Recorded here because the auto-approve predicate reads this field FIRST (`plan_readiness.is_plan_review_approved`), so a stale `no-go` is a live refusal that would have silently skipped this plan when the Set executed.
- 2026-09-16 reviewed (aw set): Reviewed 2026-09-16 by /plan-review: REVIEWED - OPEN QUESTIONS, NO-GO. 10 findings (PR-201..PR-210), 9 FIXED, PR-201 OPEN and escalated as blocking OQ-03. All five original findings reproduce; this is the best-founded child of the Set. Blocker is an omission: lifting driver_begin breaks three existing safety guards that count subprocess launch sites per driver file. Also performed E-01's census (627 logs), which shows three of four keys unobserved and oc's ses_ preference unexercisable, and found the union is not the strict superset the plan claims. Dependency edge on i3d6ml removed as unfounded.
- 2026-09-16 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO; PR-201 through PR-210 (9 FIXED, PR-201 OPEN and escalated as the new blocking OQ-03). EVERY CLAIM IN THIS PLAN'S FINDINGS TABLE REPRODUCES, which makes it the best-founded child of the Set: F-1's capability loss was confirmed BY EXECUTION (oc's reader returns `None` on an agy-shaped log where agy's returns the id), and F-2 through F-5 all verify. The defects are OMISSIONS. THE BLOCKER: lifting `driver_begin` breaks THREE existing safety guards the plan never names. Each driver file has exactly three `argv`/`cmd` subprocess sites, and `tests/test_nested_tty_noninteractive.py:172` requires at least three PER FILE (so removing one fails "call sites vanished"), `:218` requires own-plus-shared at least three (today exactly `2 + 1`), and `tests/test_lane_tool_identity.py:486` asserts the LITERAL `env=pinned_child_env()` inside each host's `driver_begin` source, which a shared definition cannot provide. Those guards encode a 1h49m TTY wedge and the `af7i6p` lane-shadowing incident, and the easy fix (lower the threshold) is one `818uru`'s own docstring already refuses in writing, so HOW to re-count them is a human's call. I ALSO PERFORMED E-01's CENSUS (627 logs), because the union's design depends on a measurement the plan deferred: `sessionID` 167,921 events / 593 files ALL `ses_`-prefixed; `conversation_id` 2 events / 2 files, both agy-produced, flat AND nested under `result`; `sessionId`, `session_id` and the whole `init` path ZERO; and ZERO logs where oc's `ses_` preference is observable. Two consequences the plan did not anticipate: E-01's own deletion clause would narrow a wire-format reader on absence-of-evidence AND silently change oc's live `_event_session_id` (a second consumer of the same constant, never mentioned); and oc's `ses_` preference is a TESTED CONTRACT rather than an observed behavior. ALSO CORRECTED: the union is NOT "a strict superset harming neither host" (executed counter-example: agy returns `conv-FIRST` where the union returns `ses_LATER`, latent since 0 of 627 logs carry that shape, but an unchosen precedence change); agy's `conversation_id` and nesting have ZERO test coverage anywhere, so F-1's headline hazard is true AND undetectable; agy carries a dead `fallback` variable; and the `executed:i3d6ml` edge is unfounded for both symbols and is REMOVED, freeing the plan to run first. Re-scoped with the guard re-count as its own E-item requiring an injected-regression demonstration, the census as a named baseline, the precedence decision pinned by a test, first-ever agy wire-format coverage, five test files fenced, and the suite baseline named (7308 passed, one load-dependent flake). NOT DECIDED, deliberately: how to re-count three shipped safety guards. Typed record at `.aw/records/reviews/20260916-rununify-05-ct4w0a-resolve-the-two-genuine-behavior-conflicts-union-the-session.review.md` with 10 findings and 5 decisions, 1 irreversible and escalated.
- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored after both conflicts were measured symbol-by-symbol and put to the maintainer, who ruled union for one and adopt-oc for the other.

## Goal

Collapse the two symbols where the hosts really behave differently, keeping every capability each side
has today: one session-id reader that understands BOTH wire formats, and one `driver_begin` that
declares the correct `aw ipd begin` baseline for an isolated turn on either host.

READ THIS BEFORE EXECUTING. The 2026-09-16 review verified every claim in this plan's Findings table
(F-1 through F-5 all reproduce) and this is the best-founded child of the Set. Two things nonetheless
block it, and both are omissions rather than errors.

FIRST, THE REVIEW PERFORMED E-01's CENSUS, and the result contradicts the union's design premises.
Scanning all 627 session logs under `.aw/records/runs/*/sessions/`:

| Shape | Occurrences | Files |
|---|---|---|
| flat `sessionID` | 167,921 events | 593 |
| flat `conversation_id` | 2 events | 2 (both agy-produced) |
| nested `result.conversation_id` | 2 events | 2 (same files) |
| flat `sessionId` | ZERO | 0 |
| flat `session_id` | ZERO | 0 |
| nested `init.<any key>` | ZERO | 0 |

Every one of the 167,921 `sessionID` values is `ses_`-prefixed, and ZERO logs carry both a prefixed and
an unprefixed value, so oc's `ses_` PREFERENCE is unexercisable in the real corpus (F-7). Three of the
four keys and one of the two nesting paths are unobserved (F-8). E-01's own rule ("a key that appears in
NEITHER host's real logs is a candidate for deletion") therefore fires on most of the union, which the
plan did not anticipate.

SECOND, LIFTING `driver_begin` BREAKS THREE GUARDS THE PLAN NEVER NAMES (F-9). Two of them count
`subprocess` launch sites PER DRIVER FILE and require at least three; each driver has exactly three
today, so removing one fails them. The third asserts the LITERAL TEXT `env=pinned_child_env()` inside
each host's `driver_begin` source, which no shared-definition-plus-wrapper arrangement can satisfy.
These are not incidental test churn: each encodes a safety property (no nested `aw` may inherit a TTY;
the tooling pin must reach the child), so satisfying them requires a deliberate decision about how the
guard should count a shared launcher, which is OQ-03.

WHAT IS UNAFFECTED AND SOUND: `extract_session_id` is closure-clean (its only module dependency is
`_SESSION_ID_KEYS`, which moves with it), needs nothing from any other child, and the ruling on it is
correct. That half can proceed once the union is designed from the census rather than from the two
source listings.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the session id reader (UNION)

EXECUTED 2026-09-17. OQ-03 was RESOLVED by the maintainer (option 2: re-base the guards on the OWNER
SET) before this ran, so both task groups were in scope. What the executor found that the plan did not
predict is recorded as F-15 through F-18 below; the load-bearing one is F-15, because the plan's premise
that `driver_begin` "needs no new injection seam" is FALSE and a pure move was therefore impossible.

- [x] E-01 RE-RUN the census at execution HEAD and compare it against the review's 2026-09-16 baseline rather than starting from nothing. Scan `.aw/records/runs/*/sessions/*.jsonl` for both hosts and record: which of the four keys appear (`sessionID`, `sessionId`, `session_id`, `conversation_id`), whether any appear NESTED under a `result` or `init` object, and whether oc's `ses_`-prefix preference is observable (that is, whether ANY single log carries both a prefixed and an unprefixed value). THE REVIEW'S BASELINE, to be confirmed or contradicted by name: 627 logs; `sessionID` 167,921 events across 593 files, ALL `ses_`-prefixed; `conversation_id` 2 events in 2 files, both agy-produced, appearing BOTH flat and nested under `result`; `sessionId`, `session_id` and every `init` nesting ZERO; and ZERO files where the `ses_` preference is observable. Do not write the union from the two source listings alone.
  - Depends on: none
  - Expected outcome: a pasted per-host census at execution HEAD, stated as agreeing with or differing from the review's baseline figures above, with any difference named per shape. Note the corpus is gitignored and box-local (F-4): from an isolated lane, report `AW_MISSING_INPUT: .aw/records/runs` rather than guessing.
  - Execution state: performed

- [x] E-02 Implement ONE `extract_session_id` in `runner_shared.py` as the UNION per the maintainer's ruling: all four keys, checked flat AND inside a nested `result` or `init` mapping, with a non-dict event skipped rather than raising. Collapse the two `_SESSION_ID_KEYS` constants into one shared 4-key tuple; it is `extract_session_id`'s ONLY module-level dependency, so the pair lifts cleanly. PRESERVE oc's `ses_`-prefix PREFERENCE and PRESERVE agy's `conversation_id` plus nesting. THREE THINGS THE REVIEW ESTABLISHED THAT CHANGE HOW THIS IS WRITTEN. (a) The union is NOT order-neutral: oc's rule scans the WHOLE file before returning a fallback while agy's returns the first hit immediately, so on a log carrying agy's `conversation_id` EARLY and a `ses_` value LATER the union returns the `ses_` value where agy returns the `conversation_id` today (F-6). That shape occurs in 0 of 627 logs, so it is latent, but it must be a STATED decision rather than an accident: record which host's answer the union changes and why that is acceptable. (b) Keep the unobserved keys and the `init` nesting DESPITE the census showing zero occurrences, because `_SESSION_ID_KEYS` is also read by oc's `_event_session_id` (`oc_runipd.py:3763`) and because deleting a key on 627 logs of evidence would be an irreversible narrowing of a wire-format reader on a sample that cannot prove absence; say so explicitly rather than invoking E-01's deletion clause (F-8). (c) Delete agy's DEAD `fallback` variable, which its body initializes and returns but can never reach non-None because every branch returns immediately (F-10).
  - Depends on: E-01
  - Expected outcome: one definition both hosts reach; one shared `_SESSION_ID_KEYS`; oc's prefix preference and agy's key/nesting coverage BOTH demonstrably intact; the order-of-precedence change stated; the retention of unobserved branches justified rather than defaulted.
  - Execution state: performed

### Task group 2: the begin baseline (ADOPT OC)

- [x] E-03 FIRST, RESOLVE THE THREE GUARDS THAT LIFTING `driver_begin` BREAKS, before writing any lift, because each encodes a safety property and none can be satisfied by a naive move. MEASURED at review: (a) `tests/test_nested_tty_noninteractive.py:172` requires at least THREE `argv`/`cmd` subprocess sites per driver FILE and each host has exactly three, so removing one yields two and fails with "call sites vanished"; (b) `:218` requires each driver's own stdin-guarded count PLUS the shared count to be at least three, and today that is exactly `2 + 1`; (c) `tests/test_lane_tool_identity.py:486` asserts the LITERAL STRING `env=pinned_child_env()` inside `inspect.getsource(driver_begin)` for BOTH hosts, which no shared-definition-plus-wrapper arrangement can satisfy, and oc's own body carries a comment saying that literal is kept visible deliberately for exactly this guard. Whichever way OQ-03 is answered, update these guards to count a SHARED launcher the way `818uru` already taught (b) to do, and say why the new counting still refuses a real regression. Do NOT weaken a threshold merely to make the suite pass.
  - Depends on: none
  - Expected outcome: the three guards updated with their new counting rule stated, plus a demonstration that each still FAILS on an injected regression (a removed `stdin=`, an unpinned env), so the safety property survives the re-count rather than being traded for green.
  - Execution state: performed

- [x] E-04 Adopt oc's `driver_begin` as the single definition, including its `isolated: bool = False` keyword and its `begin_baseline_env(isolated)` child-env overlay, and route agy's call site through it. `begin_baseline_env` moves with it and is trivial to lift (a pure one-line function with ZERO module-level dependencies, `oc_runipd.py:915`); `pinned_child_env` and `pinned_module_argv` are the other two dependencies and are ALREADY shared objects (both hosts reach the same function), so the lift needs no new injection beyond them. THIS IS A CAPABILITY AGY GAINS: `aw ipd begin` gates execution authority on the plan's in-scope paths being unambiguous in the baseline the turn will EXECUTE against, and for an isolated turn that baseline is the LANE, not the main tree. Pass `isolated=` truthfully from each host's existing knowledge; VERIFIED at review that agy's `execute_item` already binds an `isolate` variable, so the truthful value is in scope at its call site (`agy_runipd.py:3641`) and no new plumbing is needed. Do not default it to `True` for agy just to make the call sites match.
  - Depends on: E-03
  - Expected outcome: one definition; `begin_baseline_env` shared; an isolated agy turn now declares the lane baseline to `aw ipd begin`; a non-isolated turn on either host declares exactly what it does today.
  - Execution state: performed

- [x] E-05 Verify the adoption did not change the NON-isolated path on either host, since that is the path every current test exercises and a silent change there would be invisible. Compare the child env `driver_begin` builds for `isolated=False` against what each host built before this plan, and show they are equal. NOTE the review already established this is provable and cheap: `begin_baseline_env(False)` returns `{}`, and both hosts already reach ONE shared `pinned_child_env` (49 keys, equal across hosts), so `{**pinned_child_env(), **begin_baseline_env(False)} == pinned_child_env()` holds today. Paste it rather than reasoning about it.
  - Depends on: E-04
  - Expected outcome: pasted proof that `isolated=False` produces a byte-identical child env to the pre-change behavior for BOTH hosts.
  - Execution state: performed

### Task group 3: proof

- [x] E-06 Add `tests/test_rununify_conflicts.py`: both symbols resolve to the SAME OBJECT from both hosts; the session reader finds an id for EVERY key and nesting shape in the union (not merely the observed ones, since three keys and the `init` nesting are unobserved yet retained per E-02(b), and an unobserved branch with no test is exactly how it rots); the `ses_` preference still holds; `driver_begin` emits the isolated declaration when and only when `isolated=True`; and an AST scan proves neither runner re-defines either symbol. ADD THE COVERAGE GAP THE REVIEW FOUND: agy's `conversation_id` key and its `result`/`init` nesting have ZERO test coverage anywhere in the suite today (F-11), which is why F-1's "adopting oc alone silently disables agy session resume" is currently true AND undetectable. A test for agy's wire format is the durable half of this plan's value.
  - Depends on: E-02, E-04
  - Expected outcome: a suite that fails if either capability is lost, naming which one; first-ever coverage for agy's `conversation_id` and nested shapes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `begin_baseline_env(isolated)` already exists in `oc_runipd.py:915` with a docstring explaining the
  contract (`lanetruth` Order 02, `z2isfg`): `begin` gates execution authority on in-scope paths being
  unambiguous in the baseline the turn will execute against. Nothing needs inventing for E-03; the
  helper is written and only agy's route to it is missing.
- `_SESSION_ID_KEYS` is defined TWICE with different contents: `oc_runipd.py:3760` has three keys,
  `agy_runipd.py:2465` has four. The union must collapse those two constants as well as the function,
  or the next reader will re-fork from whichever constant they find first. ADDED AT REVIEW: the oc
  constant has a SECOND consumer the plan does not mention, `_event_session_id` (`oc_runipd.py:3763`),
  which reads the SAME tuple live during the turn to hand the subagent-progress observer a parent
  session id. Widening the shared tuple to four keys is INERT for it (it hard-filters on a `ses_`
  prefix, and `conversation_id` values are never prefixed, measured), but an executor who instead
  NARROWS the tuple under E-01's deletion clause would silently change that live path too. It is
  oc-only, so it does not block the lift; it is named so nobody edits the constant believing
  `extract_session_id` is its only reader.
- Both hosts' session logs live under `.aw/records/runs/<run-id>/sessions/`, which is GITIGNORED and
  box-local, so E-01's census is only possible in a primary checkout with real run history. An isolated
  lane cannot perform it; say `AW_MISSING_INPUT: .aw/records/runs` if that is where execution lands.
- THE NESTED-`aw` LAUNCH SITES ARE STRUCTURALLY GUARDED, PER FILE, and `driver_begin` is one of them.
  `tests/test_nested_tty_noninteractive.py` counts `subprocess` calls whose first argument is named
  `argv` or `cmd` and requires at least three per driver file plus stdin coverage; each driver has
  exactly three (`driver_begin`, `driver_finalize`, the agent `Popen`). `tests/test_lane_tool_identity.py`
  additionally asserts the LITERAL `env=pinned_child_env()` inside each host's `driver_begin` source.
  Both guards encode measured incidents (a 1h49m TTY wedge; a lane-shadowed tooling resolution), so they
  are re-counted deliberately (E-03) rather than adjusted to fit. See F-9 and OQ-03.
- `pinned_child_env` and `pinned_module_argv` are ALREADY single shared objects reachable identically
  from both hosts (verified: `agy_runipd.pinned_child_env is oc_runipd.pinned_child_env`), so
  `driver_begin`'s dependencies need no new injection seam. `begin_baseline_env` is a pure one-line
  function with zero module-level dependencies, so it lifts trivially alongside it.
- The execution contract forbids `git add -A`; commit only the declared `Scope-Paths`, path-scoped.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | `oc_runipd.py:3760` vs `agy_runipd.py:2465` | THE ONE CASE WHERE "OC WINS" WOULD BREAK A HOST. oc reads three flat `session*` keys; agy reads those plus `conversation_id`, and also looks inside nested `result` and `init` objects. Adopting oc alone leaves agy unable to find its own session id, which silently disables session resume (and therefore plan `b7xarm`'s one-shot defect-report re-ask, which refuses to fire without an observed session). |
| F-2 | HIGH | `extract_session_id`, both hosts | THE UNION IS NOT SYMMETRIC EITHER. oc encodes a PREFERENCE agy lacks: it returns a `ses_`-prefixed value immediately and keeps any other value only as a fallback. agy returns the first non-empty value it sees. A naive union built from agy's body would silently drop oc's preference, so the union must be built deliberately from both, not by taking the longer function. |
| F-3 | HIGH | `driver_begin`, `begin_baseline_env` | oc accepts `isolated` and passes a baseline-declaring env overlay to `aw ipd begin`; agy passes only `pinned_child_env()`. So an ISOLATED agy turn asks `begin` to gate on the wrong baseline. This is agy silently lacking a correctness feature, which is exactly the "one does A, the other NOT A" case, and it resolves toward oc. |
| F-4 | MED | `.aw/records/runs/` | The corpus needed for E-01's census is gitignored and absent inside an isolated lane. Both the census and any re-measurement must happen in a primary checkout, or be reported as `AW_MISSING_INPUT`. |
| F-5 | MED | measured at HEAD | Neither of these two symbols is currently a delegating stub on either side, unlike 14 of the Set's other shared symbols. Both are genuinely two implementations, which is why they were separated out of child 03 rather than lifted with it. **VERIFIED at review.** |

### Findings added by the 2026-09-16 plan review

ALL FIVE ORIGINAL FINDINGS REPRODUCE, which is worth stating plainly: F-1's capability loss was
confirmed by execution (oc's reader returns `None` on an agy-shaped log where agy's returns the id),
F-2's asymmetric preference is real, F-3's missing baseline declaration is real, F-4's gitignored corpus
is real (627 logs present in a primary checkout, `records/runs/` ignored at `.aw/.gitignore:14`), and
F-5 holds. The findings below are what the plan OMITTED.

| # | Sev | Where | Finding |
|---|---|---|---|
| F-6 | HIGH | `extract_session_id`, both hosts; executed at review | **THE UNION IS NOT "A STRICT SUPERSET HARMING NEITHER HOST", and that phrase appears in both the Scope line and OQ-01.** The two readers differ in RETURN DISCIPLINE, not only in key coverage: agy returns the first non-empty hit IMMEDIATELY, while oc scans the entire file and returns a non-`ses_` value only as a fallback. So on a log carrying agy's `conversation_id` early and a `ses_` value later, agy returns `conv-FIRST` today and the union returns `ses_LATER`. Executed both ways at review to confirm. That shape occurs in 0 of 627 logs, so the risk is LATENT rather than live, but the plan asserts an equivalence that does not hold and would have shipped a precedence change nobody decided. |
| F-7 | MEDIUM | E-01/E-02's preservation rationale; census of 627 logs | **oc's `ses_` PREFERENCE IS UNEXERCISABLE IN THE REAL CORPUS, so "a real oc behavior agy's version drops" (F-2) is true of the CODE and not of the DATA.** Measured: all 167,921 `sessionID` values are `ses_`-prefixed, and ZERO logs carry both a prefixed and an unprefixed value, which is the only shape where the preference decides anything. It IS covered by an existing test (`tests/test_oc_runipd.py:866`), so it is a tested contract and must be preserved; the correction is to the plan's justification, which claims observational grounding it does not have. State it as a contract, not as an observed behavior. |
| F-8 | MEDIUM | E-01's deletion clause; E-02's "drop it and record the deletion" | **E-01's OWN RULE, APPLIED TO THE CENSUS, WOULD DELETE MOST OF THE UNION, and the plan does not anticipate that.** Three of the four keys (`sessionId`, `session_id`) and one of the two nesting paths (`init`) appear ZERO times in 627 logs. E-01 says an unobserved branch "is a candidate for deletion rather than preservation" and E-02 says to drop it unless a launcher documents the shape. Followed literally, the executor would narrow a wire-format reader on the basis that 627 logs did not happen to contain a shape, which is absence-of-evidence reasoning; and `sessionId`/`session_id` are additionally read by oc's `_event_session_id` (`oc_runipd.py:3763`), a LIVE second consumer the plan never mentions. The clause must be neutralized explicitly for this symbol rather than followed. |
| F-9 | BLOCKER | `tests/test_nested_tty_noninteractive.py:172`, `:218`; `tests/test_lane_tool_identity.py:486` | **LIFTING `driver_begin` BREAKS THREE EXISTING GUARDS, NONE OF WHICH THE PLAN NAMES, and each encodes a safety property rather than a style rule.** Measured at review: each driver file has EXACTLY THREE `argv`/`cmd` subprocess sites (`driver_begin`, `driver_finalize`, the agent `Popen`); `:172` asserts at least three per file, so removing one fails with "call sites vanished". `:218` asserts each driver's own stdin-guarded count plus the shared count is at least three, and today that is exactly `2 + 1`. `:486` asserts the LITERAL TEXT `env=pinned_child_env()` inside `inspect.getsource(driver_begin)` for BOTH hosts, which a shared definition cannot provide, and oc's body carries a comment saying that literal is kept visible deliberately for this guard. The properties (no nested `aw` inherits a TTY; the tooling pin reaches the child) are ones this repository paid for: a finalize wedged 1h49m on the TTY case. Re-counting them for a shared launcher is a deliberate design act, not test churn. |
| F-10 | LOW | `agy_runipd.py:2471`, `:2497` | **agy's `extract_session_id` CARRIES A DEAD `fallback` VARIABLE.** It is initialized to `None` and returned at the end, but every branch that could assign a value returns immediately instead, so the variable can never be non-`None` at the return. It is harmless today and it is exactly the residue that makes a future reader believe agy has a fallback discipline it does not have. Delete it as part of the union rather than copying it forward. |
| F-11 | MEDIUM | the whole test suite | **agy's `conversation_id` KEY AND ITS `result`/`init` NESTING HAVE ZERO TEST COVERAGE ANYWHERE.** Grepped at review: `conversation_id` appears in no test file, and `extract_session_id` is exercised only in `tests/test_oc_runipd.py` (two cases, both oc-shaped). So F-1's central hazard, that adopting oc alone silently disables agy session resume, is currently BOTH true and undetectable by the suite. That makes new coverage for agy's wire format the most durable thing this plan can deliver, and it deserves to be an explicit outcome rather than a side effect of E-05's identity assertions. |
| F-12 | MEDIUM | `- Item-Dependencies: executed:i3d6ml` | **THE DEPENDENCY ON CHILD 03 IS UNFOUNDED for both symbols.** Closure-checked at review: `extract_session_id` references only `Path`, `json` and `_SESSION_ID_KEYS`, and `driver_begin` only `Path`, `subprocess`, `begin_baseline_env`, `pinned_child_env` and `pinned_module_argv`. None of those is among child 03's 48, and `pinned_child_env`/`pinned_module_argv` are already shared objects reachable from both hosts. So this plan waits on child 03 for nothing; the edge is removed, which frees it to run first. (This is the same unfounded-edge pattern found in child 04 on 2026-09-16.) |
| F-13 | LOW | `- Scope-Paths:` as authored | **THE FENCE OMITS EVERY EXISTING TEST FILE THE CHANGE MUST EDIT.** `driver_begin` is referenced by SEVEN test files (`test_agy_runipd_cli.py`, `test_begin_dirty_gate_scope.py`, `test_dirty_base_gate.py`, `test_lane_tool_identity.py`, `test_nested_tty_noninteractive.py`, `test_oc_runipd.py`, `test_worker_role_refusal.py`), three of which F-9 shows must change; `extract_session_id` by `test_oc_runipd.py`. The five the re-scoped plan can actually touch are now fenced. |
| F-14 | LOW | Required tests item 5 | **THE SUITE BASELINE IS UNSTATED AND ONE FAILURE IS PRE-EXISTING.** Measured at review, bare `python3 -m pytest`: `1 failed, 7308 passed, 3 skipped, 2 xfailed`. The failure is `tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130`, a 30s subprocess timeout under parallel load that passes in isolation (`7 passed in 1.13s`). Named so the executor does not chase it. |

### Findings added by the 2026-09-17 EXECUTION

Four things the plan and both review rounds missed. F-15 is load-bearing: it falsifies a premise stated
three times in this plan (the Scope line, E-04, and F-12) and it is the reason `driver_begin` could not
be lifted as a pure move.

| # | Sev | Where | Finding |
|---|---|---|---|
| F-15 | HIGH | `oc_runipd.py:550`, `:569`; `agy_runipd.py:333-337`; `runner_shared.py:31-38` | **"`pinned_child_env` AND `pinned_module_argv` ARE ALREADY SHARED OBJECTS, SO THE LIFT NEEDS NO NEW INJECTION SEAM" IS FALSE, and the same claim appears in the Scope line, in E-04 and in F-12.** Both are DEFINED in `oc_runipd` and are the only definitions in the package; agy reaches them by IMPORTING them from `oc_runipd`, which is what makes `agy.pinned_child_env is oc.pinned_child_env` return `True` and is what the review mistook for shared-module reachability. But the lift condition is closure over names `runner_shared` can RESOLVE, and it may never import a runner (`tests/test_runner_shared.py::NoRunnerImportTests`, enforced by AST at module level AND lazily). So a pure move raises `NameError`. Resolved by INJECTING both as keyword-only parameters with a one-line host wrapper each, which is the maintainer's ruled mechanism for exactly this case (`818uru` OQ-02) and is already how `run_checked` -- the OTHER nested-`aw` launcher, living in `runner_shared` -- consumes this SAME dependency. Recorded as decision `06-ct4w0a-D2`. Filed as backlog `tz1ucs`, because moving the pin helpers to a host-neutral home would make this and `driver_finalize` pure moves. |
| F-16 | MEDIUM | `tests/test_lane_tool_identity.py:430`, `:603` | **FIVE GUARDS BREAK ON THE LIFT, NOT THE THREE F-9 ENUMERATED.** Two more are the same family (a count keyed to FILES rather than to the property): the classified-site total at `:430` requires `>= 9` package-wide and fell to 8, and the per-host pinned-site count at `:603` requires agy `>= 3` and fell to 2. Measured with the guard's own `_classify_sites`: oc 6 sites and agy 4 before, oc 5 and agy 3 after, because `driver_begin`'s argv construction moved. Both re-based onto the owner set exactly as OQ-03 ruled for the other three, thresholds UNCHANGED at 9/4/3 with the shared module's sites now counted. `_classify_sites` also had to learn one new kind, `module-pinned-injected`, or a launcher moving into the shared module would read as a launcher DELETED. Recorded as decision `06-ct4w0a-D4`. |
| F-17 | MEDIUM | `agent_workflows/release_readiness.py:158`, `:179` | **TWO PRE-EXISTING NESTED-`aw` LAUNCHES HAVE NEITHER `stdin=` NOR THE `af7i6p` PIN, AND NO GUARD HAS EVER SEEN THEM.** Found by the package-wide completeness scan this plan had to add. `gate_leak_scan` and `gate_ipd_lint` each build a literal `[sys.executable, "-m", "agent_workflows", ...]` and call `subprocess.run` with no `stdin=subprocess.DEVNULL` and no `pinned_child_env`/`pinned_module_argv`. They were invisible to BOTH shipped guards because the ttywedge guard identified launchers by the first argument's NAME (`argv`/`cmd`) and scanned only the two driver files, and these pass an inline list literal in a third module. Exposure is bounded (both pass `--agent`, so the child is non-interactive on its own merits) but the protection is incidental rather than structural. NOW DETECTED, not fixed: `release_readiness.py` is outside this plan's `Scope-Paths`, so the two sites are recorded in `EXEMPT_OUTSIDE_OWNER_SET` with the reasoning and a THIRD such site now fails the suite. Filed as backlog `xzdudk`. |
| F-18 | LOW | this lane's environment; F-14 superseded | **THE SUITE BASELINE IS 7451, NOT 7308, AND A BARE RUN IN A WORKER LANE REPORTS 31 FAILURES THAT ARE PURELY ENVIRONMENTAL.** Re-measured at execution HEAD `1171f7b2` before any change: `7451 passed, 3 skipped, 2 xfailed`, zero failures, so F-14's 7308 figure and its named flake are both superseded (that flake did not fire in either run). SEPARATELY: a bare `python3 -m pytest` in this isolated lane fails 31 tests because the lane sets `AW_EXECUTION_ROLE=worker`, which `ipd_lifecycle` reads to refuse driver-only lifecycle verbs; one of the 31 asserts the condition literally (`test_driver_own_process_is_not_worker_role` -> `'worker' == 'worker'`). All 31 reproduce at the UNMODIFIED HEAD, and unsetting that one variable yields the clean 7451. Named because an executor who does not know this will mistake 31 pre-existing environmental failures for regressions from the change. |

## Proposed changes (ordered, validatable)

1. Re-run the census and compare it to the review's baseline (E-01), so preserved branches are preserved
   for a stated reason rather than for symmetry.
2. Write the union reader, keeping oc's `ses_` preference AND agy's keys/nesting, collapsing the two
   `_SESSION_ID_KEYS` constants into one, stating the precedence change and justifying the retained
   unobserved branches, and deleting agy's dead `fallback` (E-02).
3. Re-count the three structural guards that a shared launcher breaks, proving each still catches an
   injected regression (E-03).
4. Adopt oc's `driver_begin`, lifting `begin_baseline_env` with it and passing `isolated=` truthfully
   (E-04).
5. Prove the non-isolated path is byte-identical on both hosts (E-05).
6. Add the capability-preservation suite, including first-ever coverage for agy's wire format (E-06).

## Deferred / out of scope (with reason)

- The 48 no-disagreement symbols (child 03, `i3d6ml`) and the 8 host-string symbols (child 04,
  `tx6q0h`). NOTE the dependency edge on `i3d6ml` was REMOVED at review (F-12): closure-checked, neither
  symbol here needs anything child 03 owns, so this plan may run first.
- `PlanRecord`, `parse_plan_file`, `build_dynamic_manifest`: child 06.
- `execute_item`, `run_queue`, `initialize_run`, `build_parser`, `main`: children 07 through 11.
- CHANGING WHAT EITHER LAUNCHER EMITS. This plan makes the READER understand both formats; it does not
  ask either host to normalize its log shape, which would be a far larger change touching live process
  invocation.

## Scope check

- Over-scope: none. Three source files plus one new test file, two symbols.
- Under-scope, CORRECTED AT REVIEW: the original note said an unobserved nesting path would be DELETED
  unless a launcher documents it. That rule is now neutralized for this symbol (F-8), because the census
  shows THREE of the four keys and the whole `init` path unobserved, and deleting them would narrow a
  wire-format reader on absence-of-evidence across a 627-log sample while also changing oc's live
  `_event_session_id`. The union deliberately keeps speculative branches HERE and E-06 tests them, which
  is the honest trade: an untested unobserved branch rots, a tested one is cheap.
- Under-scope, ADDED AT REVIEW: this plan must also re-count three existing structural guards (F-9) and
  add the first-ever test coverage for agy's session wire format (F-11). Neither was in the original
  scope and the plan cannot land correctly without the first.

## Required tests / validation

1. `tests/test_rununify_conflicts.py` (new): object identity across hosts for both symbols; the session
   reader finds an id for EVERY key and nesting shape IN THE UNION (all four keys, flat plus `result`
   plus `init`), not merely the observed ones, since the unobserved branches are deliberately retained
   (F-8) and an untested retained branch is how it rots; the `ses_` preference still holds (a log
   containing both an unprefixed and a `ses_` value returns the prefixed one); `driver_begin` emits the
   isolated declaration if and only if `isolated=True`; AST scan proving no re-fork.
2. NON-VACUITY, THREE controls, because each ruling can regress silently: (a) drop `conversation_id`
   from the shared key list and show an agy-shaped log FAILS to resolve; (b) drop the `ses_` preference
   and show the mixed-value case FAILS; (c) drop the `result` nesting and show the nested agy shape
   FAILS. Restore all three.
3. THE PRECEDENCE DECISION PINNED (F-6): a test asserting what the union returns for a log carrying
   agy's `conversation_id` EARLY and a `ses_` value LATER, so the answer is a recorded decision rather
   than an emergent property nobody chose.
4. `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` green, both of which exercise session
   extraction and begin.
5. THE THREE RE-COUNTED GUARDS green AND still failing on an injected regression (F-9):
   `tests/test_nested_tty_noninteractive.py` (both the per-file count at `:172` and the
   own-plus-shared count at `:218`) and `tests/test_lane_tool_identity.py:486`. A green re-count that
   no longer refuses a removed `stdin=` or an unpinned env has traded a safety property for a passing
   suite, so the injected-regression demonstration is the load-bearing half.
6. `tests/test_begin_dirty_gate_scope.py` green, named because it asserts `begin_baseline_env`'s exact
   contract (`{"AW_ISOLATED_BASELINE": "1"}` when isolated, `{}` otherwise) and `driver_begin`'s
   keyword-only `isolated` parameter with a `False` default; it is the closest thing to a spec for what
   E-04 adopts.
7. `tests/test_defect_report.py` green, named specifically because plan `b7xarm`'s re-ask REFUSES when
   no session id was observed (`runner_shared.py:6040`), so a regression in this reader would disable
   that feature quietly rather than loudly.
8. Bare `python3 -m pytest`, summary pasted, at or above the 7308-passed baseline MEASURED AT REVIEW
   2026-09-16, with NO NEW failure judged against the one known flake named in F-14; if that test
   fails, show it passing in isolation rather than treating it as a regression.

## Spec / documentation sync

No `.spec.md` change. Neither symbol is spec-governed: the session-id wire format belongs to each host's
launcher, and `aw ipd begin`'s baseline contract is already described by `begin_baseline_env`'s own
docstring and by the `lanetruth` Order 02 plan that introduced it. E-04 makes agy CONFORM to that
existing contract rather than altering it, which is a defect fix and not a contract change.

CHECKED AT REVIEW 2026-09-16 and the no-change conclusion HOLDS. Verified there is no `.spec.md`
governing either symbol, and that `begin_baseline_env`'s contract is instead pinned by TESTS
(`tests/test_begin_dirty_gate_scope.py:301`-`:315`: the exact env dict for each `isolated` value, plus
`driver_begin`'s keyword-only parameter with a `False` default), which is why that file is now both
fenced and named in Required tests item 6. ONE CAVEAT WORTH STATING, since it is the closest this plan
comes to a contract change: the three guards E-03 re-counts are themselves the durable statement of two
safety properties (`c4gd2h`-adjacent TTY denial and the `af7i6p` tooling pin). Rewriting what they
ASSERT is not a spec edit, but it is a change to how a shipped invariant is enforced, so V-03 requires
the new form be shown still refusing a real regression rather than merely passing.

## Open questions

### OQ-01: For `extract_session_id`, does the maintainer's "oc is preferred" ruling mean oc's reader wins outright?

- Blocking: no
- Status: resolved
- Owner: maintainer, 2026-09-14
- Resolution or deferral rationale: NO, and the maintainer ruled explicitly on this symbol. The standing
  rule is "oc is preferred UNLESS there are significant differences (one does A the other NOT A)", and
  this is the clearest instance of that exception in the whole Set: agy reads a key and a nesting shape
  oc cannot see, and that shape IS agy's wire format. VERIFIED BY EXECUTION at review: oc's reader
  returns `None` on an agy-shaped log where agy's returns the id, so "oc wins" would break agy outright.
  The ruling is UNION. F-2 records the non-obvious half: the union must also keep oc's `ses_` preference,
  so it is built from both bodies deliberately rather than by adopting the longer one.
  ONE CLAIM IN THIS RESOLUTION IS WITHDRAWN (F-6): the union is NOT "a strict superset that harms
  neither host". The two readers differ in RETURN DISCIPLINE as well as key coverage (agy returns the
  first hit immediately; oc scans the whole file and treats a non-`ses_` value as a fallback), so on a
  log carrying agy's `conversation_id` early and a `ses_` value later the union returns the `ses_` value
  where agy returns the `conversation_id` today. Measured: that shape occurs in 0 of 627 real logs, so
  the change is LATENT and acceptable, but it is a precedence change and must be recorded as a decision
  rather than asserted away. Required tests item 3 pins whichever answer the executor chooses.

### OQ-02: For `driver_begin`, is giving agy the isolated-baseline declaration a behavior change the parent forbids?

- Blocking: no
- Status: resolved
- Owner: maintainer, 2026-09-14
- Resolution or deferral rationale: The parent forbids a child CHANGING what a runner does as a
  side effect of unification. This is the maintainer's deliberate adoption of oc's version for a symbol
  where agy is measurably deficient: an isolated agy turn currently asks `aw ipd begin` to gate on the
  main tree's baseline when the turn will execute in a lane. Fixing that is the point of the ruling, not
  an accident of it. E-05 bounds the risk by proving the NON-isolated path, which every existing test
  exercises, is byte-identical afterwards. VERIFIED at review: `begin_baseline_env(False)` returns `{}`
  and both hosts already reach ONE shared `pinned_child_env`, so that byte-identity holds today and E-05
  is cheap to discharge. Also verified that agy's `execute_item` already binds an `isolate` variable, so
  passing `isolated=` truthfully needs no new plumbing.
  THE BEHAVIOR QUESTION IS ANSWERED; A DIFFERENT QUESTION IS NOT, and it is now OQ-03: HOW to lift this
  symbol at all, given that three existing guards count subprocess launch sites per driver FILE and one
  asserts a literal source string inside `driver_begin` (F-9). That is not the behavior objection this
  OQ addresses, and nothing here is weakened by it.

### OQ-03: Lifting `driver_begin` breaks three safety guards that count launch sites per driver file. How should they be re-counted?

- Blocking: yes
- Finding: PR-201
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-16. The directive, given
  directly: "at the end of the SET, there should be one code base shared by the two runners that
  contains 100% of the otherwise redundant code that currently is duplicated between the two runners."
  That REFUSES options 3 and 4 outright: option 3 declines to lift `driver_begin` at all, and option 4
  keeps a per-host wrapper containing a real duplicated `subprocess.run` purely to satisfy a test, which
  the plan itself calls "duplication wearing a wrapper". Both leave redundancy standing at the end of
  the Set.
  THE ANSWER IS OPTION 2, the reviewer's own recommendation: RE-BASE THE GUARDS ON THE OWNER SET rather
  than on files. Enumerate every nested-`aw` launcher wherever it now lives (shared or per-host) and
  assert the TOTAL and the stdin coverage over that set. Option 1 (extend the `818uru` per-file pattern)
  is acceptable as a FALLBACK only if option 2 proves larger than this child can carry, and if taken it
  must be recorded as a deliberate narrowing with the reason, not as an equivalent choice.
  WHY OPTION 2 RATHER THAN 1, given the maintainer ruled tests are changeable: with seven more children
  in this Set moving symbols between files, a guard keyed to FILES needs an edit every time anything
  moves, and each such edit is an opportunity to weaken it by accident. A guard keyed to the OWNER SET
  states the property that actually matters ("every nested `aw` launch denies stdin, wherever it lives")
  and stops needing maintenance. That is strictly stronger, and the maintainer's ruling that tests are
  work rather than blockers is what makes the larger change available.
  THE MAINTAINER'S RULING ON TESTS, which this question needed and did not have: asked directly whether
  these source-reading guards prevent the work, the answer was that they do not. This repository has
  ALREADY adapted this exact guard for shared code once: `tests/test_nested_tty_noninteractive.py:190-203`
  counts the shared file's launch sites toward BOTH runners, its docstring records the reasoning, and all
  41 tests in that file plus `tests/test_lane_tool_identity.py` pass at this HEAD (verified 2026-09-16).
  So re-basing a guard is sanctioned work. WHAT REMAINS FORBIDDEN is what `818uru`'s docstring already
  forbids and this plan must not do: lowering a threshold so a failure disappears. The rewritten guards
  MUST keep an injected-regression test proving they still fail when a launch site loses its `stdin=`,
  and the literal-text assertion at `tests/test_lane_tool_identity.py:486` must be re-pointed at the
  shared `driver_begin` rather than deleted, so the `env=pinned_child_env()` pin survives the move.
  EXECUTED 2026-09-17, OPTION 2 AS RULED, and the result is recorded here because two details of the
  ruling could not be honored literally and both are strengthenings rather than reductions.
  FIRST, THE COUNT IS GONE, NOT RE-BASED. Option 2 said to "assert the TOTAL and the stdin coverage over
  that set". The stdin coverage is now a UNIVERSAL (every non-exempt launcher in the owner set passes
  `stdin=`, named by file and line when one does not) rather than a total, because a total can be
  satisfied while one site is uncovered. The population is pinned separately so the universal cannot go
  vacuous, and the two count-based guards in `test_lane_tool_identity.py` keep their thresholds (9, 4, 3)
  verbatim with the shared module's sites added, which is the `818uru` "own plus shared" pattern applied
  unchanged. No threshold was lowered anywhere.
  SECOND, THE LITERAL AT `:486` COULD NOT BE RE-POINTED, AND IT WAS ALREADY VACUOUS. The ruling asked
  that `env=pinned_child_env()` be re-pointed at the shared `driver_begin` rather than deleted. The
  shared body receives its env builder as an injected parameter (F-15) and so spells it `env_builder()`;
  the literal cannot appear there. MEASURED at execution HEAD: that assertion was ALREADY passing on oc
  by matching a COMMENT, not code (oc's code read `env={**pinned_child_env(), **begin_baseline_env(...)}`).
  So the pin is now asserted BEHAVIORALLY -- each host binds the real `pinned_child_env`, and the env the
  launcher hands the child carries `AW_PIN_KEEP_ROOT` and the runner root on `PYTHONPATH` -- with an
  unpinned-env control proving non-vacuity, and the vacuity measurement itself pinned as a test that
  reads the pre-change body out of git. Recorded as decision `06-ct4w0a-D3`.
  TWO MORE GUARDS BROKE THAN THE THREE THIS QUESTION NAMED (F-16), both the same file-keyed family, and
  both were re-based the same way (decision `06-ct4w0a-D4`). AND THE RE-BASE OPENED ONE NEW HOLE, which is
  closed rather than accepted: an owner-set guard cannot see a launcher in an unlisted module, so a
  package-wide semantic scan now fails when the set of outside launches changes. It immediately found two
  PRE-EXISTING unprotected nested-`aw` launches that no guard had ever seen (F-17, backlog `xzdudk`).
  Both injected-regression demonstrations the ruling required are pasted in V-03.

  THE REVIEWER'S ANALYSIS BELOW IS PRESERVED and is the specification for the re-basing work.
  --- original analysis, recommendation now ratified ---
  NOT RESOLVABLE FROM REPOSITORY EVIDENCE. The evidence establishes
  the breakage precisely; it does not establish what the guards SHOULD assert once a launcher is shared,
  and getting that wrong trades away a safety property this repository has already paid for.
  THE SYMPTOM, plainly: two of these guards exist so that no nested `aw` process can inherit the
  operator's terminal. When one did, a finalize hung for 1 hour 49 minutes waiting on input nobody could
  see, because its prompt went into a pipe. The third exists so the runner's own tooling, not whatever
  copy sits in the current directory, is what a child `aw` executes. Both properties are enforced
  STRUCTURALLY, by counting `subprocess` call sites per driver file, because that is the only way to
  catch a NEW launcher added without the protection.
  WHY LIFTING BREAKS THEM, measured at review. Each driver file has exactly three `argv`/`cmd`
  subprocess sites: `driver_begin`, `driver_finalize`, and the agent `Popen`.
  `tests/test_nested_tty_noninteractive.py:172` asserts at least three per FILE, so removing one fails
  with "call sites vanished". `:218` asserts each driver's own stdin-guarded count plus the shared count
  is at least three; today that is exactly `2 + 1`. And `tests/test_lane_tool_identity.py:486` asserts
  the LITERAL TEXT `env=pinned_child_env()` appears inside
  `inspect.getsource(driver_begin)` for BOTH hosts, which a shared definition cannot provide; oc's body
  even carries a comment saying that literal is kept visible deliberately for this guard.
  THE PRECEDENT THAT MAKES THIS ANSWERABLE BUT NOT OBVIOUS: `818uru` already faced exactly this when
  `run_checked` became shared, and its answer was to give the shared file its own count and add it to
  both sides (`:218`'s "own plus shared" form). It deliberately did NOT lower the threshold, and its
  docstring says why: lowering to 2 "would have made this pass while silently accepting a future change
  that actually removed a `stdin=`". So there is a house pattern, and applying it to a SECOND symbol is
  a judgement about how much structural coverage per file is still enough.
  The options:
  1. EXTEND THE `818uru` PATTERN: keep both thresholds at 3, count the shared file's sites toward each
     driver, and rewrite the literal-text assertion at `:486` to check the SHARED `driver_begin` source
     instead of each host's. Consistent with precedent; the per-file guard becomes weaker in the sense
     that a driver could reach 3 with fewer of its own sites.
  2. RE-BASE THE GUARDS ON THE OWNER SET rather than on files: enumerate every nested-`aw` launcher
     wherever it now lives (shared or per-host) and assert the TOTAL and the stdin coverage over that
     set. Strongest property, most work, and it stops the count from needing an edit every time a symbol
     moves, which given seven more children in this Set is a real saving.
  3. DO NOT LIFT `driver_begin` in this plan. Take only the `extract_session_id` half (which is sound and
     unblocked) and give the `driver_begin` unification its own plan alongside the guard redesign.
     Smallest risk; leaves agy's isolated-baseline defect unfixed for longer.
  4. LIFT IT AND KEEP A PER-HOST WRAPPER that still contains a real `subprocess.run` with the literal
     `env=pinned_child_env()`. Satisfies all three guards untouched, and is duplication wearing a
     wrapper, which is what this Set exists to remove.
  My recommendation is OPTION 2, with OPTION 3 as the safe fallback if the guard redesign is judged too
  large for this child. I did NOT act on either, because both change what a shipped safety guard
  asserts, and narrowing a TTY or tooling-pin guard is precisely the kind of change that should carry a
  human's signature rather than a reviewer's.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted per-host census of session-log keys and nesting observed in real logs, produced at execution HEAD, EXPLICITLY COMPARED against the review's 2026-09-16 baseline (627 logs; `sessionID` 167,921 events / 593 files all `ses_`-prefixed; `conversation_id` 2 events / 2 files both flat and nested under `result`; `sessionId`, `session_id`, `init` all zero; zero files where the `ses_` preference is observable), stating agreement or naming each difference. From an isolated lane, `AW_MISSING_INPUT: .aw/records/runs` instead.
  - Observed evidence: `AW_MISSING_INPUT: .aw/records/runs` - THE CENSUS CANNOT BE PERFORMED IN THIS
    LANE, exactly as F-4 predicted and as E-01's own expected outcome instructed. Measured at execution
    HEAD `1171f7b2` inside the isolated lane `.aw/worktrees/ct4w0a` (branch `aw/lane/ct4w0a`):

    ```
    $ ls -d .aw/records/runs
    ls: cannot access '.aw/records/runs': No such file or directory
    $ ls .aw/records/runs/*/sessions/*.jsonl 2>/dev/null | wc -l
    0
    $ find . -name "*.jsonl" -not -path "./.git/*" | wc -l
    0
    $ grep -n runs .aw/.gitignore
    14:records/runs/
    ```

    So the corpus is absent for the DOCUMENTED reason (gitignored at `.aw/.gitignore:14`, therefore
    box-local and never present on a lane branch), not because it was not looked for. Zero session logs
    of any shape exist here, so no figure of the review's baseline can be confirmed OR contradicted from
    this workspace.

    WHAT WAS DONE INSTEAD, because E-02 depended on this measurement and "unmeasurable" is not the same
    as "unconstrained". The review's 2026-09-16 baseline (627 logs; `sessionID` 167,921 events / 593
    files all `ses_`-prefixed; `conversation_id` 2 events / 2 files, flat AND nested under `result`;
    `sessionId`, `session_id`, `init` all ZERO; zero files where the `ses_` preference is observable) is
    ADOPTED AS-IS and treated as the weakest kind of evidence it can be: it is used ONLY to justify
    KEEPING branches, never to delete one. That direction matters and is the whole reason this V-item
    does not block. A census can show a shape is COMMON; it cannot show a wire format never emits one,
    so E-01's deletion clause is neutralized on principle (F-8) rather than on a count this lane could
    not reproduce. Every one of the four keys and both nestings is retained and TESTED (V-02, V-06), so
    the plan's outcome does not depend on the missing figure.
    RESULT DISPOSITION, stated because `pass` on an unperformed census would otherwise look like a
    claim nobody could check: this passes as `AW_MISSING_INPUT`, which is the outcome E-01 and this
    V-item BOTH specify for execution in an isolated lane ("From an isolated lane, report
    `AW_MISSING_INPUT: .aw/records/runs` rather than guessing"). No census figure is asserted here.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `oc_runipd.extract_session_id is agy_runipd.extract_session_id` -> `True` and `__module__` -> `agent_workflows.runner_shared`; the single collapsed `_SESSION_ID_KEYS` with its four keys; a resolved id for EACH of the four keys and EACH nesting shape (`result` and `init`), including the three keys the census never observed; the mixed-value case returning the `ses_`-prefixed value (F-2); the PRECEDENCE decision from F-6 shown by executing the early-`conversation_id`/late-`ses_` log and stating which value the union returns and why that was chosen; and confirmation that agy's dead `fallback` is gone (F-10).
  - Observed evidence: ONE definition, reached identically, with every capability of both readers
    intact and the precedence change recorded.

    ```
    === V-02: object identity + module ===
    oc.extract_session_id is agy.extract_session_id -> True
    __module__ -> agent_workflows.runner_shared
    is runner_shared.extract_session_id -> True
    === the ONE collapsed key list ===
    _SESSION_ID_KEYS = ('sessionID', 'sessionId', 'session_id', 'conversation_id')
    _SESSION_ID_NESTS = ('result', 'init')
    oc._SESSION_ID_KEYS is agy._SESSION_ID_KEYS -> True
    ```

    AN ID FOR EVERY KEY AND EVERY NESTING, including the three keys and the `init` path the census
    never observed (retained per F-8, tested so they cannot rot):

    ```
    === flat ===
      flat sessionID        -> 'id-sessionID'
      flat sessionId        -> 'id-sessionId'
      flat session_id       -> 'id-session_id'
      flat conversation_id  -> 'id-conversation_id'
    === nested ===
      result/sessionID        -> 'n-sessionID'
      result/sessionId        -> 'n-sessionId'
      result/session_id       -> 'n-session_id'
      result/conversation_id  -> 'n-conversation_id'
      init  /sessionID        -> 'n-sessionID'
      init  /sessionId        -> 'n-sessionId'
      init  /session_id       -> 'n-session_id'
      init  /conversation_id  -> 'n-conversation_id'
    === the ses_ preference (unprefixed FIRST, prefixed LATER) ===
      -> 'ses_real1'
    ```

    THE PRECEDENCE DECISION (F-6), executed rather than reasoned about, on a log carrying
    `conversation_id` EARLY and a `ses_` value LATER:

    ```
    === V-02: THE PRECEDENCE DECISION (F-6) ===
      union returns -> 'ses_LATER'
    ```

    WHICH HOST'S ANSWER MOVED AND WHY THAT WAS CHOSEN: agy's. Its pre-union body returned the FIRST
    non-empty hit, so it answered `conv-EARLY` on this log; the union adopts oc's whole-file scan with a
    `ses_` preference and answers `ses_LATER`. Chosen because oc's preference is a SHIPPED TESTED
    CONTRACT (`tests/test_oc_runipd.py::test_extract_session_id_prefers_ses_prefixed_over_nonprefixed`)
    while NOTHING anywhere pinned agy's ordering (F-11 measured zero coverage), because the standing
    maintainer ruling prefers oc absent a significant behavioral difference, and because the affected
    shape requires an OpenCode-style `ses_` id inside a log that also carries an Antigravity
    `conversation_id` (0 of 627 logs). Recorded as decision `06-ct4w0a-D1` and PINNED by
    `tests/test_rununify_conflicts.py::PrecedenceTests`, including a test asserting the answer agy's
    pre-union discipline gave, so the change is visible in the suite and not only in prose.

    AGY'S DEAD `fallback` IS GONE (F-10). Neither host holds a second body for it to live in, and in
    the shared body `fallback` is LIVE because it IS oc's discipline:

    ```
      agent_workflows.oc_runipd: 'def extract_session_id' present -> False
      agent_workflows.agy_runipd: 'def extract_session_id' present -> False
      shared body's `fallback` is LIVE (it is oc's discipline): True
    ```

    RETENTION OF THE UNOBSERVED BRANCHES IS JUSTIFIED, NOT DEFAULTED (F-8), and the justification is
    written at the definition itself: 627 logs cannot prove a wire format never emits a shape, so
    narrowing a READER on that basis is absence-of-evidence reasoning and irreversible in the direction
    that loses data; and `_SESSION_ID_KEYS` has a SECOND consumer, `oc_runipd._event_session_id`, which
    reads the same tuple LIVE during a turn. Widening to four keys is inert for it (it hard-filters on a
    `ses_` prefix, which a `conversation_id` value never carries); narrowing would have changed it.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the three re-counted guards shown GREEN, and, the load-bearing half, shown STILL FAILING on an injected regression: remove a `stdin=` from one nested-`aw` launch site and paste the named failure, then restore; unpin the env at one site and paste the named failure, then restore. Plus the new counting rule quoted from the test with a one-line statement of what it now refuses.
  - Observed evidence: FIVE guards were re-based, not three (F-16), all GREEN, and each shown to still
    refuse a real regression. OQ-03's ruled option 2 (re-base on the OWNER SET) was applied.

    GREEN, both files:

    ```
    $ python3 -m pytest tests/test_lane_tool_identity.py tests/test_nested_tty_noninteractive.py -o addopts="" -q
    .................................................                        [100%]
    49 passed in 5.92s
    ```

    THE NEW COUNTING RULE, quoted from the test, and WHAT IT REFUSES. From
    `tests/test_nested_tty_noninteractive.py`:

    ```
    OWNER_SET = DRIVERS + ("agent_workflows/runner_shared.py",)
    ```

    and the guard body no longer counts at all, it QUANTIFIES:

    ```
    self.assertEqual(uncovered, [], "nested-`aw` launch site(s) in the owner set do not deny stdin: ...")
    self.assertGreaterEqual(launchers, 4, ...)          # non-vacuity: the population is pinned
    self.assertEqual(agent_popen_exemptions, 2, ...)    # only the two agent spawns may be exempt
    ```

    IT REFUSES: any nested-`aw` launcher ANYWHERE in the owner set that does not pass `stdin=`. That is
    strictly stronger than the old `>= 3 per file`, because a count can be satisfied while one site is
    uncovered, whereas a universal cannot. The old per-file thresholds are GONE rather than lowered; the
    two remaining count-based guards in `test_lane_tool_identity.py` keep their thresholds (4 and 3)
    verbatim and simply add the shared module's sites, which is the `818uru` "own plus shared" pattern.

    THE OWNER SET AS MEASURED at execution HEAD (6 launchers, 4 stdin-covered, 2 exempt agent `Popen`s):

    ```
    ===== agent_workflows/oc_runipd.py
      L1340 driver_finalize      popen=False stdin=True
      L6325 run_opencode         popen=True  stdin=False   <- the agent spawn, exempt (backlog qyaime)
    ===== agent_workflows/agy_runipd.py
      L1074 driver_finalize      popen=False stdin=True
      L3123 run_agy_turn         popen=True  stdin=False   <- the agent spawn, exempt
    ===== agent_workflows/runner_shared.py
      L636  run_checked          popen=False stdin=True
      L7757 driver_begin         popen=False stdin=True    <- moved here by this plan
    ```

    INJECTED REGRESSION 1, A REMOVED `stdin=` (the load-bearing half). `stdin=subprocess.DEVNULL` was
    deleted from the shared `driver_begin` launch site:

    ```
    E       AssertionError: Lists differ: ['agent_workflows/runner_shared.py:7757 (arg0=cmd)'] != []
    E        : nested-`aw` launch site(s) in the owner set do not deny stdin: agent_workflows/runner_shared.py:7757 (arg0=cmd)
    FAILED tests/test_nested_tty_noninteractive.py::CallerDevnullTests::test_every_nested_aw_run_denies_stdin
    FAILED tests/test_nested_tty_noninteractive.py::CallerDevnullTests::test_symmetry_across_both_drivers
    2 failed, 18 passed in 3.44s
    ```

    RESTORED and green (`20 passed in 3.77s`). Note the failure NAMES the file and line, which the old
    per-file count could not do: it would only have said a total dropped.

    INJECTED REGRESSION 2, AN UNPINNED ENV. oc's wrapper was changed to bind
    `env_builder=lambda: dict(os.environ)` instead of the pin:

    ```
    E       AssertionError: 'env_builder=pinned_child_env' not found in '...env_builder=lambda: dict(__import__("os").environ)...'
    E        : oc_runipd.driver_begin must bind the shared pin as its env_builder
    FAILED tests/test_lane_tool_identity.py::TheBeginPinSurvivedTheMove::test_each_host_binds_the_real_pin_into_the_shared_launcher
    1 failed, 28 passed in 2.09s
    ```

    RESTORED and green (`62 passed in 4.25s` with the new suite).

    THE LITERAL-TEXT GUARD, AND WHY ITS REPLACEMENT IS STRONGER RATHER THAN WEAKER (decision
    `06-ct4w0a-D3`). OQ-03 asked that `env=pinned_child_env()` at `tests/test_lane_tool_identity.py:486`
    be "re-pointed at the shared `driver_begin` rather than deleted". The literal cannot survive
    verbatim, because the shared body receives its env builder as a parameter and spells it
    `env_builder()`. MEASURED, and this is the finding that decided the replacement: THE OLD ASSERTION
    WAS ALREADY VACUOUS ON OC at execution HEAD:

    ```
    pre-change oc driver_begin, literal 'env=pinned_child_env()':
      in RAW source (what the shipped guard read) : True
      in CODE ONLY  (comments stripped)          : False
    the only match in RAW was this COMMENT line:
      # guard (tests/test_lane_tool_identity.py) asserts the literal `env=pinned_child_env()`
    ```

    oc's code read `env={**pinned_child_env(), **begin_baseline_env(isolated)}`, which does not contain
    that substring; the guard was passing on oc by matching the comment that explained it. So the
    replacement asserts the PROPERTY in two halves: each host BINDS the real `pinned_child_env`
    (regression 2 above proves it fails otherwise), and the env the shared launcher actually hands the
    child CARRIES the pin's markers (`AW_PIN_KEEP_ROOT` and the runner root on `PYTHONPATH`), with an
    unpinned-env control showing that assertion is not vacuous. The vacuity measurement itself is pinned
    as a test (`test_the_old_text_search_was_vacuous_on_oc`) reading the pre-change body out of git, so
    this claim is re-derivable rather than folklore. `driver_finalize`'s half of the original guard is
    UNCHANGED, because `driver_finalize` is still per-host and out of scope.

    THE NEW HOLE THE RE-BASE OPENS, AND THE GUARD THAT CLOSES IT. An owner-set guard cannot see a
    launcher in an unlisted module, which is worse than the per-file counting it replaced. So
    `OwnerSetCompletenessTests` scans the WHOLE package by MEANING (a function that builds a nested-`aw`
    argv through the pin helpers or a literal `-m agent_workflows`) and fails when the set of outside
    launches changes. That scan immediately found two PRE-EXISTING unprotected sites (F-17, filed as
    backlog `xzdudk`), which no previous guard had ever seen.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted identity result for `driver_begin` AND for `begin_baseline_env`; the child env `driver_begin` builds for `isolated=True` on BOTH hosts showing `AW_ISOLATED_BASELINE=1` present; and the pasted agy call site showing `isolated=` receiving the truthful `isolate` value rather than a literal.
  - Observed evidence: one launcher, both dependencies shared, agy declaring the lane baseline for the
    first time.

    ```
    === V-04: identity ===
      begin_baseline_env: oc is agy -> True | __module__ -> agent_workflows.runner_shared
      shared driver_begin reached by both -> True
      __module__ of the shared launcher -> agent_workflows.runner_shared
      host driver_begin holds NO subprocess body:
        agent_workflows.oc_runipd: 'subprocess.run' in wrapper -> False
        agent_workflows.agy_runipd: 'subprocess.run' in wrapper -> False
    ```

    NOTE HONESTLY WHAT IS AND IS NOT IDENTICAL, because the plan asked for "pasted identity result for
    `driver_begin`": `oc_runipd.driver_begin is agy_runipd.driver_begin` is **False**, and that is
    CORRECT rather than a shortfall. Each host keeps a one-line WRAPPER at the original name and
    signature, because the launcher's two dependencies (`pinned_child_env`, `pinned_module_argv`) are
    defined in `oc_runipd` and `runner_shared` may never import a runner (F-15, decision
    `06-ct4w0a-D2`). The de-duplication claim is therefore asserted as: exactly ONE launcher BODY
    exists in the package (neither wrapper contains `subprocess.run`, shown above), and both hosts
    reach the SAME shared object (`True`, shown above). That is the maintainer's ruled shape for an
    injected dependency (`818uru` OQ-02) and is identical to how `run_checked`, the other nested-`aw`
    launcher, already lives in `runner_shared`.

    THE ISOLATED DECLARATION, on BOTH hosts:

    ```
    === V-04: the child env for isolated=True on BOTH hosts ===
      agent_workflows.oc_runipd:  AW_ISOLATED_BASELINE='1' keys=53
      agent_workflows.agy_runipd: AW_ISOLATED_BASELINE='1' keys=53
    ```

    AGY'S CALL SITE PASSES THE TRUTHFUL VALUE, not a literal. `isolate` is the run's own flag, bound at
    `agy_runipd.py:3594` and the SAME flag that allocates the lane below, so begin and the execution
    tree cannot disagree:

    ```
    3594:    isolate = state.get("options", {}).get("isolate_worktree", True)
    ...
    3763-        if isolate:
    3764:            begin_rc, begin_msg = driver_begin(repo, item["id6"], actor, isolated=True)
    3765-        else:
    3766:            begin_rc, begin_msg = driver_begin(repo, item["id6"], actor)
    ```

    The non-isolated branch keeps the exact pre-existing three-argument call shape, so a
    `--no-isolate-worktree` agy run sends what it always sent. Both branches are pinned by
    `tests/test_rununify_conflicts.py::BeginBaselineTests::test_agys_call_site_passes_the_truthful_isolate_value`,
    and the fail-closed ordering (begin BEFORE the lane exists) is now asserted for BOTH hosts where it
    was previously asserted for oc only.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted byte-comparison of the `isolated=False` child env before and after the change, for both hosts, showing equality (and the key count, so an empty-dict false pass is visible).
  - Observed evidence: byte-identical on both hosts, with key counts so an empty-dict false pass is
    visible.

    ```
    === V-05: isolated=False is BYTE-IDENTICAL to the bare pinned env (both hosts) ===
      agent_workflows.oc_runipd:  equal=True keys_before=52 keys_after=52 AW_ISOLATED_BASELINE_present=False
      agent_workflows.agy_runipd: equal=True keys_before=52 keys_after=52 AW_ISOLATED_BASELINE_present=False
      begin_baseline_env(False) == {}

    === V-05: the two hosts build the SAME env (one shared pinned_child_env) ===
      oc.pinned_child_env is agy.pinned_child_env -> True
      envs equal -> True
    ```

    52 keys before and after, not zero, so the equality is over a populated dict. The `isolated=True`
    case adds exactly one key (53, shown in V-04), which bounds the change to the isolated path. This is
    also asserted permanently, not just here, by
    `tests/test_rununify_conflicts.py::BeginBaselineTests::test_the_non_isolated_child_env_is_byte_identical_to_the_bare_pin`
    (including the key-count assertion), because every OTHER test in the suite exercises the
    non-isolated path and a silent change there would be invisible.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: FOUR parts, all pasted. (a) `python3 -m pytest tests/test_rununify_conflicts.py -o addopts=""` green. (b) ALL THREE non-vacuity controls from Required tests item 2, each failing when its capability is removed and green when restored. (c) The NEW agy-wire-format coverage named test by test, since F-11 measured it at ZERO today, plus a demonstration that it fails against oc's reader (proving it tests the capability rather than the union's mere existence). (d) Bare `python3 -m pytest` at or above 7308 passed with no new failure judged against F-14's named flake, plus `tests/test_defect_report.py` and `tests/test_begin_dirty_gate_scope.py` green by name.
  - Observed evidence: FOUR parts.

    (a) THE NEW SUITE GREEN:

    ```
    $ python3 -m pytest tests/test_rununify_conflicts.py -o addopts="" -q
    .................................................................       [100%]
    33 passed in 2.18s
    ```

    (b) THE NON-VACUITY CONTROLS, FOUR rather than the three the plan required (the `init` nesting got
    one too, since it is retained-but-unobserved and therefore the likeliest branch to rot). Each is a
    deliberately crippled REPLICA of the shared body run over the same fixture, so no shared state is
    mutated where a parallel worker could observe it:

    ```
    NonVacuityControlTests::test_control_a_dropping_conversation_id_breaks_the_agy_shape PASSED
    NonVacuityControlTests::test_control_b_dropping_the_ses_preference_breaks_the_mixed_case PASSED
    NonVacuityControlTests::test_control_c_dropping_the_result_nesting_breaks_the_nested_shape PASSED
    NonVacuityControlTests::test_control_d_dropping_the_init_nesting_breaks_the_retained_shape PASSED
    ```

    Each control asserts BOTH directions in one test: the crippled reader returns `None` (or the wrong
    value, for (b)) AND the real reader still resolves correctly, which is the "restore" half. THE
    CONTROLS ARE THEMSELVES GUARDED by `ControlFidelityTests`, which asserts the UNCRIPPLED replica
    agrees with the real function across all seven fixture shapes; without that, a replica could drift
    into proving something about a strawman.

    (c) THE FIRST-EVER AGY WIRE-FORMAT COVERAGE (F-11 measured it at ZERO), named test by test, each
    additionally shown to FAIL against oc's pre-union reader:

    ```
    AgyWireFormatTests::test_flat_conversation_id_resolves_and_oc_alone_would_have_missed_it PASSED
    AgyWireFormatTests::test_conversation_id_nested_under_result_resolves PASSED
    AgyWireFormatTests::test_conversation_id_nested_under_init_resolves PASSED
    AgyWireFormatTests::test_a_realistic_agy_log_resolves_end_to_end PASSED
    AgyWireFormatTests::test_oc_wire_format_still_resolves_too PASSED
    ```

    THE PROOF THAT THESE TEST THE CAPABILITY AND NOT THE UNION'S EXISTENCE: each of the four agy-shape
    tests asserts `_oc_pre_union_reader(log) is None` on the same fixture. That reconstruction of oc's
    pre-union body is itself verified against the SHIPPED body read out of git at HEAD `1171f7b2`
    (`ControlFidelityTests::test_the_pre_union_oc_replica_matches_the_shipped_body_it_reconstructs`), so
    the "oc would have missed it" claim is checked against real history rather than against memory.
    This is F-1's central hazard made DETECTABLE for the first time.

    (d) THE WHOLE SUITE, BARE:

    ```
    $ python3 -m pytest
    7492 passed, 3 skipped, 2 xfailed in 163.52s (0:02:43)
    ```

    THE BASELINE IS RE-MEASURED, AND F-14's FIGURE IS SUPERSEDED. The plan required "at or above 7308
    passed", measured at the 2026-09-16 review. At this execution HEAD the pre-change baseline is
    **7451 passed, 3 skipped, 2 xfailed, zero failures**, so 7492 is +41 (the new file's 33 plus the 8
    added to the two re-based guard files) with ZERO failures and zero regressions. F-14's named flake
    (`test_sigint_produces_the_report_and_exits_130`) did NOT fire in either run.

    ONE ENVIRONMENTAL CAVEAT, STATED PLAINLY BECAUSE IT AFFECTS HOW THESE NUMBERS WERE PRODUCED (F-18).
    A bare `python3 -m pytest` in this lane reports **31 failures** BEFORE any change in this plan, and
    all 31 are caused by the lane's own `AW_EXECUTION_ROLE=worker` marker, which `ipd_lifecycle` reads to
    refuse driver-only lifecycle verbs. One of them asserts the condition directly:
    `tests/test_worker_role_refusal.py::ChildEnvWorkerRoleTests::test_driver_own_process_is_not_worker_role`
    -> `AssertionError: 'worker' == 'worker'`. Unsetting that one variable yields the clean 7451 above,
    so every suite figure in this evidence was produced with `env -u AW_EXECUTION_ROLE`. This is a
    property of the worker lane, NOT of this change, and the identical 31 failures reproduce at the
    unmodified HEAD.

    THE NAMED FILES, green:

    ```
    $ python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_begin_dirty_gate_scope.py tests/test_defect_report.py -o addopts="" -q
    322 passed in 41.50s
    ```

    `tests/test_begin_dirty_gate_scope.py` is the closest thing to a spec for what E-04 adopted (it pins
    `begin_baseline_env`'s exact env dict per `isolated` value and `driver_begin`'s keyword-only
    parameter with a `False` default) and it passes UNMODIFIED, which is the strongest single signal that
    the adoption preserved the contract. `tests/test_defect_report.py` is green too, so the `b7xarm`
    re-ask (which REFUSES when no session id was observed) is not disabled by the reader change.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. EVALUATED AT REVIEW 2026-09-16 rather than inherited. The plan is
  genuinely two independent concerns (a reader union and a launcher adoption) in three task groups, and
  each E-item is one focused pass. The revision ADDS one item (the guard re-count, E-03) because it is a
  distinct deliverable with its own test-surface that the original plan folded invisibly into the
  adoption. Note the two halves are separable and one is unblocked: task group 1 depends on nothing that
  OQ-03 governs, which is what makes option 3 there viable.
- A density advisory (`IPD-Z602`) fires on E-02 at the review-finalize checkpoint. It was EVALUATED, not
  dismissed, and it is a fair reading of the text: E-02 carries three lettered clauses. They are
  CONSTRAINTS ON ONE DELIVERABLE rather than three deliverables. The deliverable is the single shared
  union function; (a) requires its precedence choice be stated, (b) requires its retained-but-unobserved
  branches be justified rather than silently dropped, and (c) deletes a dead variable inside the very
  body being replaced. All three touch one function, produce one definition, and are verified by one
  `V-*` item (V-02). Splitting them would separate a decision from the code that embodies it, which is
  the opposite of the intent. The advisory is informational and does not affect the conforming
  disposition; the only error at this checkpoint is the deliberate `IPD-Q501` from OQ-03.

OQ-03 IS OPEN AND `Blocking: yes`. `aw ipd lint` refuses this plan at every checkpoint until the
maintainer answers it, including `aw ipd begin`. The question is HOW to re-count three shipped safety
guards once a launcher is shared; narrowing a TTY or tooling-pin guard should carry a human's signature.

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS, restated after the 2026-09-16 review:

1. F-9 / OQ-03, THE GUARD RE-COUNT. This is the one place where making the suite green is easy and
   WRONG: lowering a threshold from 3 to 2 turns both TTY guards into decoration, and `818uru`'s
   docstring already records that reasoning and refuses it. V-03's injected-regression demonstration is
   the only thing that distinguishes a correct re-count from a traded-away safety property.
2. F-11, THE ABSENT COVERAGE. agy's `conversation_id` and its nesting have ZERO tests today, so F-1's
   central hazard is real AND invisible. Verify the new tests fail against oc's reader, or they prove
   only that the union exists.
3. F-6, THE PRECEDENCE CHANGE. The union is not the strict superset the plan claims; confirm the
   executor RECORDED which host's answer changes rather than discovering it later from a resumed run.
4. F-2's `ses_` preference, which no existing agy test would notice losing, and the `b7xarm` coupling in
   Required tests item 7, since a quiet regression here disables the defect-report re-ask by making it
   believe no session was observed.
