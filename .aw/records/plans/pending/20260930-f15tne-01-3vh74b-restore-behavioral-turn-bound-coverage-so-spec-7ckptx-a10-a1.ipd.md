# IPD: Restore behavioral turn-bound coverage so spec 7ckptx A10, A10b, A10c and A10d are demonstrated by executed outcomes

- Date: 2026-09-30
- Kind: child
- Concern: THE WHOLE R4.4 DRIVER-BOUND SURFACE HAS ZERO TEST COVERAGE, and it is the surface that stops an unattended turn wedging forever. MEASURED at HEAD `e9d397a4`: searching `tests/` and `tools/` for `TurnBoundWatch`, `bound_expiry_record`, `driver_bound_for_host`, `parse_host_ceiling_seconds`, `BOUND_MAX_TURN`, `BOUND_PERMISSION`, `MAX_TURN_TIMEOUT`, `PERMISSION_TIMEOUT`, `HOST_CEILING_OFFSET_SECONDS`, `BOUND_EXPIRY_DISPOSITION` and `note_permission_request` returns ZERO hits for every one of those eleven symbols. Only `bound_expiry_reaper` is named at all, by `tests/test_reap_contract.py` (a `typing.get_type_hints` signature-binding check) and `tests/test_lane_reaper_callshape.py` (keyword-binding call-shape spies); neither ever starts a bound, so no test in the suite proves a bound FIRES. Plan `lhmrhx` delivered spec `7ckptx` A10 into `tests/test_turn_bounds.py` (2417 lines); commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") deleted that file whole, taking `tests/test_lane_permission_posture.py` with it. So `7ckptx` is an APPROVED, release-blocking (`- Blocks-Release: next`) spec whose A10, A10b, A10c and A10d are currently undemonstrated, and a regression in `TurnBoundWatch` would be caught by nothing.
- Scope: Add ONE new test file, `tests/test_turn_bounds.py`, holding behavioral coverage for the four named criteria, every assertion driven by EXECUTING the code (real `subprocess.Popen` children that are actually killed, real driver launchers, real `argparse` parsers) and NONE by reading production source. Covers: the max-turn and permission bounds firing on a real child through the DEFAULT shared reaper (A10); the constants' names, defaults, zero-disables and uniform arming across isolated and non-isolated turns, plus the non-isolated prompt's byte-identity (A10b); the recorded finding that the permission detector is unproven, ships disabled, and has ZERO production callers, while still working when armed (A10c option (ii)); and the antigravity overlap being attributable by measurement (A10d). EXCLUDES A10e, A11, and every criterion outside A10/A10b/A10c/A10d, which the backlog item does not ask for. EXCLUDES wiring `note_permission_request` into either driver: that is a product change this test-restoration plan must not make, and it is filed as a carrier (see Deferred).
- Scope-Paths: tests/test_turn_bounds.py
- Item-Dependencies: none
- Status: reviewed
- From-Spec: 7ckptx
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: f15tne
- Set: f15tne
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 3vh74b

## Workflow history
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review PR-806: add the machine-readable From-Spec link. The plan cites spec 7ckptx as the governing contract throughout (its title, Concern, Goal, Spec sync section and all four criteria), but carried no - From-Spec: field, so aw check reported the advisory check.plan-spec-link-missing and the spec-to-plan handoff was prose-only rather than machine-readable. 7ckptx is approved and carries - Blocks-Release: next, so a resolvable link matters: it is the field a release-gate carrier check reads. No other change.
- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-801 (HIGH), PR-802, PR-803, PR-804, PR-805 all FIXED, zero deferred, zero open. Structural lint conforming with ZERO diagnostics and ZERO advisories at --phase author and --phase review-finalize. THIS IS AN EXCEPTIONALLY WELL MEASURED PLAN AND ITS DESIGN SURVIVES INTACT: review re-EXECUTED every route rather than re-reading it, at HEAD f82d7ea53, and F1 through F4, F7, F8 and F10's substantive claim all reproduce. Both real-child kills reproduce (max rc=-2 elapsed=0.481 fired max-turn-timeout; perm rc=-2 elapsed=0.415 fired permission-timeout), each writing disposition failed-safely and emitting one turn-bound-expired event; all four reset/corpse/bookkeeping properties reproduce; every constant and all the host arithmetic reproduce including has PERMISSION_DEADLINE False; both prompt renderings reproduce verbatim. F7 is live in this very turn (OPENCODE_CONFIG_CONTENT is ambient in my own environment and conftest pops AW_EXECUTION_ROLE but not it), so E-04's hermeticity requirement is justified. The deferred carrier 4xtpvg exists and is open. THE ONE HIGH FINDING WOULD HAVE MADE THE NEW FILE RED ON ITS FIRST RUN. PR-801: E-01 requires asserting the child's wait completes INSIDE THE BOUND'S OWN WINDOW, which is false. TurnBoundWatch.__init__ carries check_interval=1.0 and the thread loop is while not self._stop.wait(self.check_interval), so expiry is noticed AT A POLL TICK; against a 0.3s bound the first tick is at 1.0s and elapsed is POLL-DOMINATED (measured 0.475s at the default, 0.382s at check_interval=0.05, both firing correctly). The word check_interval appeared ZERO times in the plan, so the number governing the timing envelope of its slowest tests was invisible. Fixed in E-01 and V-01 with the correct assertion shape plus new F12. TWO CITATION DEFECTS in findings the plan leans on: PR-802, F10's claim that git log -S returns exactly one commit is wrong (it returns FIVE, because -S counts occurrence changes in any tracked file including the deleted TEST file and plan prose) though the zero-caller fact is CORRECT on the call-site search; PR-803, F9's 72 option strings reproduces under no accessor tried (recursive walk gives 225 oc / 197 agy) though the ABSENCE of all four flag spellings does reproduce. PR-804: baseline drifted 172 (3387 authored, 3559 measured, both fully green), so all bars are now by node id. PR-805: build_turn_budget_notice takes a STATE DICT not a ceiling float, so V-05's required paste needed the real call shape. ALSO VERIFIED FOR THE EXECUTOR'S BENEFIT (F15): V-07's mutation matrix is achievable cell by cell, including the non-obvious arity of the _expired stub, and cell (d) produces the REQUIRED SPLIT. No production file modified; every mutation applied via mock.patch.object in a throwaway process and the tree left clean. Findings and four Decisions rows in .aw/records/reviews/20260930-f15tne-01-3vh74b-restore-behavioral-turn-bound-coverage-so-spec-7ckptx-a10-a1.review.md.

- 2026-09-30 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `f15tne`, whose 2026-09-28 maintainer ruling is that restored coverage "must test observable outcomes (real subprocess execution, timeout deadlines, exit disposition) rather than inspecting source code or pinning script text". EVERY route in this plan was EXECUTED against HEAD `e9d397a4` before being written down, and the measurements are pasted in Findings; no E-item proposes a mechanism that has not been shown to work. Two authoring measurements CHANGED the plan rather than decorating it. FIRST, the deleted file's A10c and A10d tests read `lane_containment`'s own source with `inspect.getfile(...).read_text()` to assert its docstrings, which `GUIDING_PRINCIPLES.md` P16 now prohibits outright, so this plan does NOT restore them and F5/F6 record what is consequently NOT re-asserted and why that is honest rather than a silent loss. SECOND, the deleted file carried a KNOWN ambient-environment defect with a twenty-three-filing history (backlog `cfgj8s`, `wnabns`, `mepbmp`, `tem4g9`, `4vn040`, `wx72g3`, `1ixbnr`), fixed by executed plan `heglfv` INSIDE the file that `19313eed` then deleted; the fix therefore no longer exists, and F7 reproduces the failure in THIS lane (my own turn exports `OPENCODE_CONFIG_CONTENT`), so E-04 re-derives hermeticity explicitly and V-04 requires it be proven in both ambient directions.
- 2026-09-30 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Leave `spec 7ckptx` A10, A10b, A10c and A10d demonstrated by tests that KILL REAL PROCESSES and DRIVE REAL
LAUNCHERS, so a regression in the driver-side bounds turns a test red instead of silently removing the only
supervision an unattended turn has.

The test of success is not "a file named `tests/test_turn_bounds.py` exists again". It is that each new test
is shown to FAIL when the behavior it names is broken (the mutation check V-07 owns), and that not one
assertion in the file reads production source, counts callers, or pins a docstring.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the expiry path, proven by killing real processes (A10)

- [ ] E-01 CREATE `tests/test_turn_bounds.py` AND PROVE BOTH BOUNDS KILL A REAL CHILD THROUGH THE DEFAULT SHARED REAPER. This is the criterion the backlog item cares about most and the one a fake process cannot establish. For EACH bound, spawn a genuine `subprocess.Popen([sys.executable, "-c", "import time\nwhile True: time.sleep(0.05)"])`, which is both SILENT (so it could never be caught from the driver's blocking read loop, which is why the watch is a thread) and IMMORTAL (so only a real kill ends it). Construct `TurnBoundWatch` with `reap=lane_containment.bound_expiry_reaper(process, run_dir, item)` and NO `reap=` override on the inner call, so the DEFAULT reaper is exercised and the termination is genuinely attributable to `runner_shutdown.clean_shutdown` (spec `c4gd2h` R5's single reaper) rather than to a test double. Then assert on OUTCOMES: `process.wait(timeout=20)` returns a NEGATIVE returncode (signal death, measured `-2`), `watch.fired` is the expected `BOUND_MAX_TURN` / `BOUND_PERMISSION` constant, `item["turn_bound_expiry"]["bound"]` names the same one, and its `disposition` is `BOUND_EXPIRY_DISPOSITION` (`"failed-safely"`).
  DO NOT ASSERT THAT THE WAIT COMPLETES "INSIDE THE BOUND'S OWN WINDOW", WHICH IS FALSE AND WOULD MAKE THIS TEST RED AT ITS FIRST RUN (F12). `TurnBoundWatch.__init__` takes a `check_interval` defaulting to `1.0` and its thread loop is `while not self._stop.wait(self.check_interval)`, so expiry is NOTICED ONLY AT A POLL TICK, never at the instant the bound elapses. Against a 0.3s bound the FIRST tick is at 1.0s, so elapsed is POLL-DOMINATED, not bound-dominated: review measured `check_interval` default -> `rc=-2 elapsed=0.475`, and `check_interval=0.05` -> `rc=-2 elapsed=0.382`, both firing correctly. (The authored `0.415s`/`0.417s` figures reproduce in the same range.) The correct assertions are therefore `elapsed >= bound` as the LOWER bound and a generous ceiling well above `bound + check_interval`; state the `check_interval` you pass (or that you accept the 1.0 default) in the test, since it is the number that decides the timing envelope. A tight upper bound here is the single most likely way this file arrives flaky under `-n auto`. Measured at authoring: max-turn with `max_turn_timeout=0.3` gave `rc -2` in `0.415s`; permission with `permission_timeout=0.3` after `note_permission_request()` gave `rc -2` in `0.417s`. FOR THE PERMISSION CASE, ENCODE A10's "DEMONSTRABLY NOT AT THE COARSE NO-PROGRESS BOUND" AS AN ASSERTION RATHER THAN A COMMENT: set `max_turn_timeout=0` and pick a nominal stall figure at least 20x the permission window (authoring used `STALL=6.0` against `PERM=0.3`), assert that ratio in the test body so the margin cannot be silently eroded, and assert the observed elapsed time is under it. Note that `bound_expiry_reaper`'s default reaper PRINTS a `clean shutdown:` report to stderr when invariants are unsatisfied (measured: `ledger_coherent` is NOT satisfied because a bare `tmp_path` has no `state.json`); that output is expected, is not a failure, and the test must not assert it absent.
  - Depends on: none
  - Expected outcome: `tests/test_turn_bounds.py` exists with both real-subprocess tests passing; pasted output showing, per bound, the negative returncode, the elapsed seconds, `watch.fired`, and the `bound`+`disposition` read back off the item; the permission test's `assert PERM * 20 <= STALL` present in the body.
  - Execution state: pending

- [ ] E-02 PROVE THE THREE EXPIRY-PATH PROPERTIES THAT NEED NO REAL CHILD, WITHOUT WEAKENING E-01. These are separated from E-01 deliberately: they are about the RECORD and the RESET SEMANTICS rather than about killing a process, they run in milliseconds, and folding them into E-01 would make one test assert four unrelated things. (a) THE RESET ASYMMETRY, which `TurnBoundWatch`'s docstring calls "the whole design": with only the permission bound armed, `note_permission_request()` then `note_progress()` then a sleep PAST the window must leave the reap UNCALLED (measured: `{}`); with only the max-turn bound armed, calling `note_progress()` in a tight loop must NOT prevent the fire (measured: fired `max-turn-timeout`). That second half is the property that makes this bound worth having beside the no-progress watchdog, so it is asserted directly. (b) THE DEAD CHILD IS NOT REAPED TWICE: with `is_alive=lambda: False` and a `0.05s` bound, sleeping `0.3s` must record ZERO reap calls (measured: `[]`), because the watch must return rather than reap a corpse. (c) BOOKKEEPING FAILURE MUST NOT BLOCK THE REAP: point `bound_expiry_reaper` at an unwritable run dir (authoring used a path containing a NUL byte, which makes the `events.jsonl` append raise) and assert the injected reaper still ran (measured: `['r']`). Case (c) is the one place in this plan an injected `reap=` double is CORRECT rather than a shortcut, because the property under test is that the reap survives a recording error, and observing that needs a spy; the injected double must keep the `(process, *, run_dir)` keyword shape `_ReapCallable` declares, or the call raises `TypeError` for an unrelated reason.
  - Depends on: E-01
  - Expected outcome: three passing tests; pasted output for each of (a), (b), (c) showing respectively the empty-then-fired pair, the empty reap list, and the `['r']` spy list.
  - Execution state: pending

### Task group 2: the bounds are named, defaulted and uniformly armed (A10b)

- [ ] E-03 ASSERT THE NAMES, DEFAULTS AND ZERO-DISABLES BY READING THE LIVE MODULE ATTRIBUTES, NOT THE SOURCE. A10b requires the constants be spelled `PERMISSION_TIMEOUT` and `MAX_TURN_TIMEOUT` (not `..._DEADLINE`), that `MAX_TURN_TIMEOUT` default to 4 hours and `PERMISSION_TIMEOUT` to `0`, and that both accept `0` to disable. Assert with `hasattr`/`getattr` on the imported module and with `assert not hasattr(lane_containment, "PERMISSION_DEADLINE")`, which interrogates the OBJECT rather than the text and so is not a P16 pin: a rename genuinely breaks an importer, which is the contract being defended. Measured at authoring: `PERMISSION_TIMEOUT == 0.0`, `MAX_TURN_TIMEOUT == 14400.0` (`== 4*60*60`), `HOST_CEILING_OFFSET_SECONDS == 300.0`, `BOUND_PERMISSION == "permission-timeout"`, `BOUND_MAX_TURN == "max-turn-timeout"`, `BOUND_EXPIRY_DISPOSITION == "failed-safely"`. For the zero-disable half, assert BEHAVIOR rather than the value: `TurnBoundWatch(reap=..., max_turn_timeout=0, permission_timeout=0).enabled is False` (measured `False`), and confirm no thread fires by entering that watch and observing no reap. ALSO assert `BOUND_EXPIRY_DISPOSITION` is a value both drivers' reconcile machinery already understands, by checking it against the shipped terminal-status vocabulary rather than hardcoding the string a second time; if no importable vocabulary exposes it, assert the literal and say so in a comment rather than inventing an accessor. DO NOT restore the deleted file's docstring assertions (it parsed `#:` comment blocks out of `lane_containment.py` with `inspect.getfile(...).read_text()` to prove each constant documents its measured-from instant and reset semantics); P16's "no text, banner, or docstring pins" prohibits that outright, and F5 records that this criterion clause is consequently left to review rather than re-asserted mechanically.
  - Depends on: E-01
  - Expected outcome: passing tests asserting each constant's value and the absence of the `..._DEADLINE` spellings; `enabled is False` for the both-zero construction plus a shown-empty reap list; pasted values for all six constants; no `read_text`/`inspect.getfile`/`ast` call anywhere in the new file (verified by search, pasted).
  - Execution state: pending

- [ ] E-04 DRIVE BOTH REAL LAUNCHERS AND PROVE THE BOUND IS ARMED IDENTICALLY FOR AN ISOLATED AND A NON-ISOLATED TURN, HERMETICALLY. This is A10b's "armed for a NON-isolated turn as well as an isolated one" and it cannot be established without running the launcher, because the arming site sits inside `run_opencode` / `run_agy_turn`. For each host, call the real launcher twice (`work_dir=<lane>` and `work_dir=None`) with `subprocess.Popen` patched to a stub yielding an empty stdout and `lane_containment.TurnBoundWatch` patched to a spy that RECORDS its kwargs and delegates to the real class, then assert exactly ONE watch is constructed per turn with the SAME positive `max_turn_timeout` on both. Measured at authoring: oc armed `14400.0` on both; agy armed `14100.0` on both (the offset value, which is E-06's subject). The oc launcher additionally needs `observe_opencode_policy` stubbed, or the R4.2 probe spawns a real host. HERMETICITY IS REQUIRED, NOT OPTIONAL, AND IT IS WHY THIS E-ITEM IS THE RISKIEST ONE HERE. If the test also contrasts the isolation-scoped permission POLICY (present when isolated, absent when not) it MUST NOT read the ambient environment: `run_opencode` builds the child env from `os.environ`, an OpenCode-hosted agent exports `OPENCODE_CONFIG_CONTENT` itself, and the assertion then fails for every lane agent while passing in a clean shell and in CI. That exact defect was filed at least SEVEN times (`cfgj8s`, `wnabns`, `mepbmp`, `tem4g9`, `4vn040`, `wx72g3`, `1ixbnr`; `cfgj8s` records twenty-three filings of one non-hermetic assertion) and was fixed by executed plan `heglfv` inside the very file `19313eed` deleted, so THE FIX NO LONGER EXISTS IN THE TREE. It reproduced in THIS authoring lane: with the variable ambient, the non-isolated env showed the key PRESENT; with `env -u OPENCODE_CONFIG_CONTENT`, ABSENT (F7). So either scrub the variable per-test with `monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)` before driving, or omit the policy contrast entirely and assert only the bound arming, which is what A10b actually demands. DO NOT add a session-wide `conftest.py` scrub for it: `cfgj8s` explicitly REJECTS that mechanism ("what made rolevac `8i0xa7`'s role guard vacuous"), and `conftest.py`'s own note records that it scrubs `AW_EXECUTION_ROLE`, `AW_RUN_ID` and `AW_ITEM_ID6` and deliberately not this one.
  - Depends on: E-01
  - Expected outcome: per host, pasted spy output showing exactly one watch per turn and equal positive `max_turn_timeout` for isolated and non-isolated; if the policy contrast is kept, the pasted per-test `delenv` line and the test passing BOTH with the variable ambient and with `env -u OPENCODE_CONFIG_CONTENT`; if it is omitted, that choice stated in the test's docstring with `cfgj8s` cited.
  - Execution state: pending

- [ ] E-05 PROVE THE NON-ISOLATED PROMPT IS STILL BYTE-IDENTICAL AND NAMES NEITHER BOUND. A10b requires this and the reason is structural rather than decorative: R4.4a claims an exception to R1.3's byte-identity rule, and the exception is only safe because these bounds are driver-side supervision that changes no instruction an agent reads. For each host, build the prompt twice through the real `build_prompt` (once with no lane argument, once with the explicit `lane_root=None`) and compare SHA-256 digests, then assert the emitted text contains neither `MAX_TURN_TIMEOUT` nor `PERMISSION_TIMEOUT` nor `lane-submissions`. Measured at authoring: identical on both hosts, and all three strings absent from both. NOTE THE ONE SUBTLETY A REVIEWER SHOULD CHECK RATHER THAN TAKE ON TRUST: the prompt DOES carry a turn-budget sentence built by `runner_shared.build_turn_budget_notice`, which renders the ceiling as a NUMBER (measured: "after 14400 seconds (about 4 hours) in total regardless of progress", and "14100 seconds (about 3.9 hours)" for the agy ceiling). So the emitted text is influenced by the bound's VALUE even though it never names the CONSTANT, and the byte-identity claim here is between two builds at the same value, NOT a claim that changing `MAX_TURN_TIMEOUT` leaves the prompt untouched. Assert the former and state the latter in the docstring; asserting the stronger thing would be false.
  - Depends on: E-01
  - Expected outcome: passing per-host test with the two digests pasted and shown equal, the three absent strings shown, and the docstring stating the value-sensitivity limit; a pasted `build_turn_budget_notice` rendering for one nonzero ceiling, so the limit is demonstrated rather than merely described. CALL IT WITH A STATE DICT, NOT A FLOAT (F14): the signature is `build_turn_budget_notice(state: dict)` reading `state["options"]["turn_ceiling"]`, so `build_turn_budget_notice({'options': {'turn_ceiling': 14100.0}})` is the shape; a bare float raises `AttributeError`.
  - Execution state: pending

### Task group 3: the unproven detector and the host overlap (A10c, A10d)

- [ ] E-06 ASSERT THE ANTIGRAVITY OVERLAP IS ATTRIBUTABLE BY MEASUREMENT (A10d). A10d asks that the relationship between the host's `240m` `--print-timeout` and the driver's `MAX_TURN_TIMEOUT` be stated, naming which fires first, and that a post-mortem be able to attribute a termination. THE "IS IT DOCUMENTED" HALF IS NOT RESTORABLE AS A TEST and this plan does not fake it: the deleted file asserted the prose with `inspect.getfile(driver).read_text()`, which P16 forbids (F6). What IS testable is the BEHAVIOR the prose describes, and that is what to assert: `parse_host_ceiling_seconds(agy_runipd.DEFAULT_TIMEOUT)` is `14400.0` (so `"240m"` is parsed as minutes, not read as 240 bare SECONDS, which would kill every turn after four minutes); `driver_bound_for_host(14400.0)` is `14100.0`, strictly LESS than the host ceiling, so the driver fires FIRST; the gap equals `HOST_CEILING_OFFSET_SECONDS` exactly; `driver_bound_for_host(None)` is unreduced `14400.0`, since OpenCode has no host-enforced equivalent; and an unparseable ceiling returns `None` and leaves the driver bound at its own default (measured: `parse_host_ceiling_seconds("banana") is None`, and the resulting bound is `14400.0`), which is the fail-toward-the-LONGER-bound direction the docstring requires because guessing short kills healthy turns. Then close the loop on ATTRIBUTION behaviorally, which is A10d's actual point: reuse E-01's real-child harness once with the max-turn bound and assert the recorded `item["turn_bound_expiry"]["bound"]` names `max-turn-timeout` specifically, so a post-mortem reading that record can tell the driver killed the turn rather than an opaque host timeout.
  - Depends on: E-01
  - Expected outcome: passing test with all five `driver_bound_for_host`/`parse_host_ceiling_seconds` measurements pasted, including the `14100.0 < 14400.0` ordering and the exact `300.0` gap; the attribution assertion shown reading a real expiry record.
  - Execution state: pending

- [ ] E-07 RECORD A10c OPTION (ii) HONESTLY: THE DETECTOR IS UNPROVEN, SHIPS DISABLED, AND HAS ZERO PRODUCTION CALLERS, YET WORKS WHEN ARMED. A10c offers two routes and forbids the cheap middle: a test that feeds a SYNTHETIC line the detector was written against does NOT satisfy it, "because that proves the regex matches itself rather than that the shape ever reaches stdout". Option (i) needs a real provoked permission ask, which this plan cannot produce and must not pretend to. So take option (ii) and assert its three parts BEHAVIORALLY. (a) THE DEFAULT REMAINS DISABLED: `PERMISSION_TIMEOUT == 0.0`, and a watch constructed with defaults (no `permission_timeout=` argument) never fires a permission expiry even with a pending ask noted, which is stronger than reading the constant because it proves the default propagates into the live object. (b) OFF BY DEFAULT IS NOT UNIMPLEMENTED: the mechanism must work the day detection is proven, which E-01's permission case already demonstrates by arming it explicitly; assert here only that the DEFAULT construction differs from the armed one, so nobody "simplifies" the bound away. (c) THE STRONGER FACT THIS PLAN MEASURED, which the deleted file did not assert and which a reviewer should weigh: `note_permission_request` has ZERO production call sites. Measured at HEAD `e9d397a4`, searching `agent_workflows/` and `tools/` returns only its own `def` and one docstring mention; both drivers call `turn_bounds.note_progress()` on every stdout line but NOTHING ever calls `note_permission_request()`, so the permission bound could not fire in production even if `PERMISSION_TIMEOUT` were set to 30. State that in the test's docstring as the recorded finding A10c option (ii) asks for, and assert the CONSEQUENCE the spec names: that `MAX_TURN_TIMEOUT` is therefore the only bound covering a permission deadlock. DO NOT assert the caller count itself, which would be the census pin P16 forbids and would break the day someone correctly wires it; assert instead that the max-turn bound alone terminates a real wedged child with no permission observation made at all, which is the same claim in behavioral form and stays true after wiring. File the wiring gap as a carrier (see Deferred); do NOT fix it here.
  - Depends on: E-01
  - Expected outcome: passing tests for (a) and (b); the docstring recording the unproven-detector finding AND the zero-caller measurement with its date and HEAD; (c) asserted as a real-child max-turn kill with no `note_permission_request()` call anywhere in that test; the carrier id6 for the wiring gap recorded in Deferred.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `GUIDING_PRINCIPLES.md` P16 ("Test outcomes and behavior, never code structure or text") is the controlling rule and it is stricter than the deleted file was written against. It prohibits `inspect.getsource`, `inspect.getsourcelines`, `ast.parse`, `read_text()` and substring/regex searches against production code; caller/definition COUNT pins; text, banner and docstring pins; and architectural placement pins. Its one narrow exception is "where the text or file itself is the artifact under test", which does not cover any assertion in this plan.
- P16 also requires MUTATION SENSITIVITY explicitly: "A test is only valid if breaking the underlying behavior makes the test fail." That is why V-07 exists and is not optional.
- The suite runs BARE: `pyproject.toml` `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`. Adding `-n0`, a second `-q`, or `-p no:randomly` is forbidden by the execution contract. `-n auto` matters for E-01: the tests sleep for real, so keep each bound in the sub-second range, and do not assume serial execution or a quiet machine when choosing the upper wait bound (authoring used a 20s `wait` timeout against 0.3s bounds, a ~60x margin).
- `conftest.py` scrubs `AW_EXECUTION_ROLE`, `AW_RUN_ID` and `AW_ITEM_ID6` from the session at import time, and deliberately does NOT scrub `OPENCODE_CONFIG_CONTENT`. Backlog `cfgj8s` explicitly rejects a session-wide scrub of it, citing rolevac `8i0xa7`, where that mechanism made a role guard vacuous.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measurements taken in this lane at HEAD `e9d397a4` unless stated otherwise.

**F1. THE COVERAGE HOLE IS TOTAL, not partial.** Searching `tests/` and `tools/` for each R4.4 symbol:

```
bound_expiry_reaper              tests=2 tools=0
bound_expiry_record              tests=0 tools=0
driver_bound_for_host            tests=0 tools=0
BOUND_MAX_TURN                   tests=0 tools=0
BOUND_PERMISSION                 tests=0 tools=0
MAX_TURN_TIMEOUT                 tests=0 tools=0
TurnBoundWatch                   tests=0 tools=0
PERMISSION_TIMEOUT               tests=0 tools=0
parse_host_ceiling_seconds       tests=0 tools=0
HOST_CEILING_OFFSET_SECONDS      tests=0 tools=0
BOUND_EXPIRY_DISPOSITION         tests=0 tools=0
note_permission_request          tests=0 tools=0
```

The two `bound_expiry_reaper` files are `tests/test_reap_contract.py` (binds the `reap` annotation's signature against the product call via `typing.get_type_hints`) and `tests/test_lane_reaper_callshape.py` (spies proving `run_dir` binds by keyword and that an omitted `reap` reaches `runner_shutdown.clean_shutdown`). Neither constructs a `TurnBoundWatch` or starts a bound, so the backlog item's characterization is confirmed: the CONTRACT is guarded and the BEHAVIOR is not.

**F2. THE CONSTANTS AND THE HOST ARITHMETIC, read off the live module.**

```
PERMISSION_TIMEOUT 0.0
MAX_TURN_TIMEOUT 14400.0
HOST_CEILING_OFFSET_SECONDS 300.0
BOUND_PERMISSION permission-timeout BOUND_MAX_TURN max-turn-timeout
BOUND_EXPIRY_DISPOSITION failed-safely
parse 240m -> 14400.0
parse junk -> None
driver_bound_for_host(None) -> 14400.0
driver_bound_for_host(14400) -> 14100.0
agy host ceiling (240m) = 14400.0 driver bound = 14100.0 driver fires first: True
gap seconds = 300.0 == HOST_CEILING_OFFSET_SECONDS: True
```

**F3. A REAL CHILD IS GENUINELY KILLED, THROUGH THE DEFAULT SHARED REAPER.** With no `reap=` override, so `runner_shutdown.clean_shutdown` is the reaper:

```
clean shutdown: lock_released, ledger_coherent, tree_observed NOT satisfied
  children_reaped (R1): ok - reaped [491810]
  lock_released (R2): SKIPPED - no run lock held by this caller
  ledger_coherent (R3): NOT SATISFIED - no ledger at /tmp/.../run/state.json
  tree_observed (R4): SKIPPED - no repository supplied
child rc -2 elapsed 0.415 watch.fired max-turn-timeout 0.3
```

and the record written onto the item, with the event line:

```
{"bound": "max-turn-timeout", "timeout_seconds": 0.3, "disposition": "failed-safely",
 "at": "...", "scope": "one turn (not one run)", "detail": "the driver's max-turn-timeout bound
 expired after 0s and terminated the child through the one shared reaper; ..."}
EVENT {"at": "...", "event": "turn-bound-expired", "id6": "f15tne", ...}
```

The permission bound behaves identically when armed: `rc -2 elapsed 0.417 fired permission-timeout < STALL: True`, record `bound: permission-timeout disposition: failed-safely`. NOTE the `detail` string renders `after 0s` for a sub-second bound, because it formats with `{timeout:.0f}`; that is cosmetic, it is not what any assertion here keys on, and it is NOT in this plan's scope to change.

**F4. THE RESET SEMANTICS, THE CORPSE GUARD AND THE BOOKKEEPING GUARD all behave as documented.**

```
permission disarmed by progress (expect empty): {}
max-turn survives repeated note_progress: {'bound': 'max-turn-timeout'}
dead child reaped again (expect []): []
reap still happened despite unwritable run dir: ['r']
```

**F5. A10b's DOCSTRING CLAUSE IS NOT RESTORABLE AS A TEST, and this plan says so rather than faking it.** A10b's last sentence asks that each constant's docstring be PASTED showing what instant it measures from and whether anything resets it. The deleted file discharged this by reading `lane_containment.py` with `inspect.getfile(...).read_text()` and asserting phrases in the `#:` blocks. P16 prohibits exactly that ("No text, banner, or docstring pins"). The docstrings DO currently satisfy the clause (`PERMISSION_TIMEOUT` states "MEASURED FROM: the instant a permission request is observed" and "RESET BY: observed progress ... RESETTABLE"; `MAX_TURN_TIMEOUT` states "MEASURED FROM: child process start, ONCE" and "RESET BY: NOTHING"), so the criterion is MET in the artifact; what changes is that it is verified by a human reading the spec against the code, not by a test. E-02(a) asserts the BEHAVIOR those docstrings describe, which is the part a test can own.

**F6. THE SAME APPLIES TO A10d's "DOCUMENTED" HALF.** The deleted file asserted `"honest limit"` and `"not a hardened boundary"` appeared in each driver's lowercased source, and its own docstring conceded this was "DELIBERATELY KEPT AS A TEXT ASSERTION, because the deliverable IS the sentence". Under P16 that is not available. The prose is present today (both `oc_runipd.py` and `agy_runipd.py` carry the R4.4d overlap note at their `turn_bounds` construction, and `lane_containment.MAX_TURN_TIMEOUT` carries the ANTIGRAVITY OVERLAP paragraph naming `driver_bound_for_host` as the resolution), so again the criterion is met in the artifact. E-06 asserts the measurable consequence instead.

**F7. THE DELETED FILE'S AMBIENT-ENV DEFECT IS LIVE AGAIN, and it reproduced in this authoring lane.** Driving `run_opencode` twice with the variable ambient (my own turn exports it) showed `OPENCODE_CONFIG_CONTENT` present in the NON-isolated child env, which is precisely the assertion that was filed as a bug at least seven times. Re-run under `env -u OPENCODE_CONFIG_CONTENT -u AW_EXECUTION_ROLE`:

```
oc  iso max_turn: [14400.0] main max_turn: [14400.0] | iso policy: True  main policy: False | iso role: worker main role: None
agy iso max_turn: [14100.0] main max_turn: [14100.0] | iso policy: False main policy: False | iso role: worker main role: None
```

Two things follow. FIRST, the BOUND half (what A10b needs) is identical isolated and non-isolated on BOTH hosts and is insensitive to the ambient variable, so E-04's required assertion is safe. SECOND, the POLICY contrast is ambient-sensitive and is the historical flake; it is optional here and must be scrubbed per-test if kept. Note also that `iso policy` is `False` for agy, which is correct and not a defect: R4.1 records that antigravity has NO denial posture, so only the oc host sets the key.

**F8. THE PROMPT IS BYTE-IDENTICAL AND NAMES NEITHER CONSTANT, with one subtlety.**

```
oc  identical: True | MAX_TURN_TIMEOUT in prompt: False | PERMISSION_TIMEOUT in prompt: False | lane-submissions in prompt: False
agy identical: True | MAX_TURN_TIMEOUT in prompt: False | PERMISSION_TIMEOUT in prompt: False | lane-submissions in prompt: False
```

The subtlety, which E-05 must state rather than paper over: `runner_shared.build_turn_budget_notice` renders the ceiling's VALUE into the prompt, so the text is value-sensitive even though it names no constant:

```
'Turn budget: this turn is terminated after 900 seconds with no observed progress, and after
 14400 seconds (about 4 hours) in total regardless of progress; ...'
'... after 14100 seconds (about 3.9 hours) in total regardless of progress; ...'   # agy ceiling
```

**F9. NO CLI FLAG OR CONFIG KNOB EXISTS FOR EITHER BOUND** (A10e's territory, measured because it was cheap and because it tells an executor not to add one): NONE of `--permission-timeout`, `--max-turn-timeout`, `--permission-deadline`, `--absolute-timeout` is registered on either host. Review re-measured and confirms all four absent, walking the `cli._build_parser()` subparser tree for the `oc` and `agy` nouns. THE AUTHORED "72 option strings" FIGURE DOES NOT REPRODUCE under any accessor review tried (the recursive walk gives 225 for `oc` and 197 for `agy`, and the hosts' own module-level parsers give 2 each), so the COUNT is unreliable and must not be re-cited or asserted; what is verified is the ABSENCE of all four flag spellings. That matters beyond tidiness: A10e asks for a negative-direction proof, and a wrong census figure is exactly the kind of number a later reader would turn into a brittle assertion. A10e is deliberately OUT of this plan's scope (the backlog item names A10, A10b, A10c, A10d), so no E-item claims it; this finding exists so a reviewer knows the surface is currently clean and so nobody "helpfully" adds a knob while restoring tests.

**F10. THE PERMISSION BOUND HAS NO PRODUCTION TRIGGER AT ALL**, which is stronger than A10c's "detection is unproven" and is the most consequential thing this plan measured. Searching `agent_workflows/` and `tools/` for `note_permission_request(` returns only its own `def` in `lane_containment.py` and one docstring reference; review re-ran this and confirms ZERO call sites (`rg -n '\.note_permission_request\(' agent_workflows/ tools/` returns nothing). CORRECTION TO THIS FINDING'S GIT CLAIM, which review measured wrong as authored: `git log -S'note_permission_request('` does NOT return "exactly one commit". It returns FIVE at review HEAD (`e03c4ee4d`, `19313eed7`, `ba4f205b2`, `8a491d4c1`, `bfa81215c`), because `-S` counts occurrence-count changes in ANY tracked file and this string moves with the deleted TEST file and with plan prose, not only with production code. `8a491d4c1` is indeed the commit that introduced the method, and the SUBSTANTIVE claim (no production caller has ever existed) survives; the citation supporting it does not, so do not repeat the one-commit figure. The durable evidence is the call-site search over `agent_workflows/` and `tools/`, not a `-S` count. Both drivers call `turn_bounds.note_progress()` on every stdout line, but nothing arms the permission bound. So `PERMISSION_TIMEOUT` is doubly disabled: the default is `0`, and even set to 30 it could not fire. This is consistent with A10c option (ii)'s recorded finding and with `PERMISSION_TIMEOUT`'s own docstring ("`MAX_TURN_TIMEOUT` is currently the ONLY bound covering a permission deadlock"), so it is not a new defect; it is the current, deliberate state, and E-07 records it behaviorally.

**F11. BASELINE SUITE STATE**, so the executor can gate on "no NEW failures" rather than on an absolute number. The authoring run at HEAD `e9d397a4`:

```
3387 passed, 2 skipped, 3 warnings in 178.67s (0:02:58)
NOTE: 207 tests were deselected by -m/-k and did not run
```

AND THE REVIEW RUN, pasted because it proves the number is a LIVE POPULATION rather than a bar. At HEAD `f82d7ea53`:

```
3559 passed, 2 skipped, 3 warnings in 195.65s (0:03:15)
NOTE: 208 tests were deselected by -m/-k and did not run
```

That is a drift of 172 collected tests and one more deselected in under two days, in a tree many lanes are changing. Both runs are FULLY GREEN, so "no NEW failures" is the right bar and the absolute totals are context only. Re-derive your own baseline at the execution HEAD and compare FAILING NODE IDS; do not reconcile against 3387 or 3559.

**F12. `check_interval` DEFAULTS TO 1.0s AND GOVERNS THE TIMING ENVELOPE, WHICH THE PLAN ORIGINALLY DID NOT MENTION AT ALL.** `TurnBoundWatch.__init__` carries `check_interval: float = 1.0` and the watch thread is `while not self._stop.wait(self.check_interval)`, so an expired bound is NOTICED AT A POLL TICK, not at the instant it elapses. Against E-01's 0.3s bounds the first tick is at 1.0s, so the observed elapsed time is POLL-DOMINATED. Measured by review on a real child: `check_interval` default -> `rc=-2 elapsed=0.475 fired='max-turn-timeout'`; `check_interval=0.05` -> `rc=-2 elapsed=0.382 fired='max-turn-timeout'`. BOTH fire correctly, so E-01's design works, but E-01's authored instruction to assert "the wait completes inside the bound's own window" is FALSE and would have made the new file red on its first run. The word `check_interval` appeared ZERO times in the plan as authored. E-01 now states the correct assertion shape (lower bound at the bound, generous ceiling above `bound + check_interval`) and requires the interval used to be stated.

**F13. EVERY EXECUTABLE ROUTE IN THIS PLAN WAS INDEPENDENTLY RE-DRIVEN AT REVIEW AND REPRODUCES.** Beyond F12's correction, review re-executed rather than re-read: both real-child kills (`max rc=-2 elapsed=0.481 fired='max-turn-timeout'`, `perm rc=-2 elapsed=0.415 fired='permission-timeout'`), each writing the expected record (`disposition: "failed-safely"`, `timeout_seconds: 0.3`, `scope: "one turn (not one run)"`) and emitting one `turn-bound-expired` event carrying the item's id6; the `clean shutdown:` stderr report with `children_reaped (R1): ok - reaped [...]` and `ledger_coherent (R3): NOT SATISFIED`, exactly as E-01 warns; all four F4 properties (`permission disarmed by progress: {}`, `max-turn survives repeated note_progress: fired max-turn-timeout`, `dead child reaped again: []`, `reap despite unwritable run dir: ['r']`); the both-zero disable (`enabled False`, empty reap list); all of F2's constants and host arithmetic including `has PERMISSION_DEADLINE: False`; and F8's two prompt renderings verbatim. So the plan's measurements are trustworthy and its two authored arithmetic errors (F9's count, F10's git figure) are citation defects rather than design defects.

**F15. V-07's MUTATION MATRIX IS ACHIEVABLE AS SPECIFIED, verified cell by cell at review so the executor is not asked for evidence nobody has shown obtainable.** This matters because V-07 calls itself the decisive evidence and a matrix that cannot be produced would stall execution. All three mutation cells were driven by `monkeypatch`/`mock.patch.object` with NO edit to `agent_workflows/`: (b) `TurnBoundWatch._expired` stubbed to always return `None` leaves the real child ALIVE and unreaped (`rc='TIMEOUT(survived)' elapsed=3.00 fired=None record=None`), so E-01's returncode and `fired` assertions both trip, which is the required failure shape rather than an unrelated timeout; (c) `driver_bound_for_host` stubbed to return `MAX_TURN_TIMEOUT` gives `14400.0` so the strict `<` ordering is False, tripping exactly E-06's ordering/gap assertion; (d) `note_progress` stubbed to a no-op produces the REQUIRED SPLIT, with half one firing `permission-timeout` despite progress (so that half fails) while half two still fires `max-turn-timeout` (so that half passes), which is precisely the isolation V-07 demands and is not merely assumed. Note the stub for (b) must accept the `now` argument (`lambda self, now: None`), since `_expired` is called as `self._expired(time.monotonic())`.

**F14. `build_turn_budget_notice` TAKES A STATE DICT, NOT A CEILING, so V-05's "paste a rendering for one nonzero ceiling" needs the real call shape.** Its signature is `build_turn_budget_notice(state: dict[str, Any]) -> str` and it reads `state["options"]["turn_ceiling"]`, falling back to `lane_containment.MAX_TURN_TIMEOUT`. Review called it correctly and reproduced F8's renderings exactly: `build_turn_budget_notice({})` yields "... after 900 seconds with no observed progress, and after 14400 seconds (about 4 hours) in total ...", and `{'options': {'turn_ceiling': 14100.0}}` yields "14100 seconds (about 3.9 hours)". Also measured, and worth knowing because it bounds what E-05 may claim: with BOTH bounds disabled (`stall_timeout: 0, turn_ceiling: 0`) the function returns the EMPTY STRING, so the notice is omitted rather than rendered with zeros. An executor passing a bare float gets `AttributeError: 'float' object has no attribute 'get'`, which is a wasted cycle the plan can prevent by naming the shape.

## Proposed changes (ordered, validatable)

1. E-01 creates the file with the two real-subprocess kill demonstrations (A10's core), because every later item reuses that harness.
2. E-02 adds the three record/reset properties that need no child, keeping them separate from E-01's slow tests.
3. E-03 adds the constant and zero-disable assertions read off the live module (A10b, part).
4. E-04 drives both real launchers for the uniform-arming proof (A10b, part), with hermeticity handled explicitly.
5. E-05 adds the prompt byte-identity proof with its honest value-sensitivity limit (A10b, part).
6. E-06 adds the host-overlap arithmetic and the attribution assertion (A10d).
7. E-07 adds the unproven-detector record and the max-turn-is-the-only-cover assertion (A10c option (ii)).

## Deferred / out of scope (with reason)

- WIRING `note_permission_request` INTO EITHER DRIVER. F10 measures that the permission bound has no production trigger, so `PERMISSION_TIMEOUT` could not fire even if armed. That is a PRODUCT change with a real risk profile (a false positive kills a healthy turn, which is exactly why R4.4b ships the bound disabled), and it requires the stdout detection A10c option (i) demands and nobody has produced. A test-restoration plan must not make it.
  - Carrier: 4xtpvg
  Filed at authoring rather than deferred to execution, so the gap is tracked whether or not this plan runs. It records F10's measurement verbatim (the zero-caller search, the single introducing commit `8a491d4c`, the consequence that `MAX_TURN_TIMEOUT` is the only cover) and the precondition that spec `7ckptx` A10c option (i) must be satisfied before the bound may be armed.
- A10e (NO NEW CONFIGURATION SURFACE) AND A11 (the in-lane lifecycle refusal). Backlog `f15tne` names A10, A10b, A10c and A10d, and these are different criteria with their own surfaces (a parser census and a lifecycle-verb refusal respectively). F9 records that A10e's surface is currently clean, so nothing is silently rotting while it waits.
  - Carrier-Declined: A10e is measured clean today (F9) and A11's `lane_containment`-adjacent behavior is a different requirement (R4.5); filing a carrier would assert outstanding work that measurement does not support. If the maintainer wants those criteria demonstrated too, they are a separate item.
- RESTORING `tests/test_lane_permission_posture.py`, which `19313eed` deleted in the same commit. It covers R4.1/R4.2 permission posture, not R4.4 bounds, and is outside this item's stated scope.
  - Carrier-Declined: not named by backlog `f15tne`, and folding a second spec area into this plan would make an A10 restoration into a general posture restoration. Worth its own item if the maintainer wants it.
- RE-ASSERTING A10b's DOCSTRING CLAUSE AND A10d's "DOCUMENTED" CLAUSE MECHANICALLY (F5, F6). Both were text pins and P16 prohibits them.
  - Carrier-Declined: the underlying prose is PRESENT in the artifact today (quoted in F5 and F6), so there is no work outstanding; what changed is the verification method, and asserting it with a text pin would violate the repository's own standing rule. Recorded so a reviewer checking A10b/A10d line by line knows which clause is human-verified rather than test-verified.

## Scope check

- Over-scope: TWO RISKS NAMED. FIRST, an executor reaching F10 may be tempted to WIRE `note_permission_request` into the drivers, since the gap is glaring and the fix looks small; do not, for the reason in Deferred, and note that doing so would also make E-07(c)'s assertion measure something different from what it says. SECOND, an executor may want to add a session-wide `OPENCODE_CONFIG_CONTENT` scrub to `conftest.py` to make E-04 easy; do not, because `cfgj8s` rejects that mechanism by name and `conftest.py` is not in `- Scope-Paths:`.
- Under-scope: this plan restores FOUR criteria, not the deleted file. The deleted `tests/test_turn_bounds.py` was 2417 lines and also covered A10e, A11, the zero-work retry machinery, the host-truncation signal and the requeue dispatch path, none of which is R4.4 bound coverage and none of which backlog `f15tne` asks for. It also leaves A10b's docstring clause and A10d's documentation clause human-verified rather than test-verified (F5, F6), and it does NOT close the `note_permission_request` wiring gap it discovered (F10). Stated so a reviewer weighs a known limit rather than discovering it.

## Required tests / validation

1. `python3 -m pytest` BARE, before and after, both summary lines pasted. Bare means bare: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, a second `-q` compounds to `-qq` and suppresses the `N passed` line this contract requires, and `-n0` makes the suite several times slower here. Gate on NO NEW failures BY NODE ID, never on an absolute count, and re-derive the before-run yourself: F11 now records TWO baselines that already disagree (`3387 passed` at authoring HEAD `e9d397a4`, `3559 passed` at review HEAD `f82d7ea53`, a drift of 172), both fully green, so neither total is a bar.
2. `python3 -m pytest tests/test_turn_bounds.py -v` after the change, showing every new test BY NAME and passing, so the file's contents are visible rather than inferred from a total.
3. THE HERMETICITY CHECK, in BOTH directions, which is the flake this file historically had: `python3 -m pytest tests/test_turn_bounds.py` must pass with `OPENCODE_CONFIG_CONTENT` AMBIENT (set it explicitly if the executing shell lacks it) and under `env -u OPENCODE_CONFIG_CONTENT`. A pass in only one direction does not satisfy V-04.
4. THE MUTATION CHECK, V-07, which is the decisive evidence and the one this plan cannot be reported done without. P16 requires it directly ("A test is only valid if breaking the underlying behavior makes the test fail").
5. A pasted search over the new file showing ZERO uses of `inspect.getsource`, `inspect.getsourcelines`, `inspect.getfile`, `ast.parse`, `ast.walk`, `ast.unparse`, and zero `read_text()` against any `agent_workflows/` path. This is the backlog item's central constraint, so it is verified rather than asserted.
6. `aw ipd lint --phase pre-transition` conforming, pasted.
7. `aw sanitize --agent` clean, pasted. Not pro forma: the new tests write `tmp_path`-derived absolute paths and spawn subprocesses whose output may carry them.
8. No production file modified: `git status --porcelain` pasted, showing only `tests/test_turn_bounds.py` (plus this plan's own lifecycle changes).

## Spec / documentation sync

No spec amendment is owed, and that is measured rather than assumed. `- Scope-Paths:` declares one test file
and no `.spec.md`. This plan changes NO behavior any spec describes: it adds tests that demonstrate criteria
spec `7ckptx` already states, which is the spec being SATISFIED rather than amended.

Two things a reviewer might mistake for spec work, named so they are not re-litigated. FIRST, F5 and F6 record
that A10b's docstring clause and A10d's documentation clause are left human-verified rather than
test-verified, because P16 forbids the text pins the deleted file used. That is a statement about VERIFICATION
METHOD, not a request to weaken either criterion, and the underlying prose is present in the artifact today
(quoted in both findings). No amendment is proposed, and an executor who believes one IS required must declare
the `.spec.md` in `- Scope-Paths:` before editing it, since both runners announce declared spec edits at run
start and reconcile them at finalize. SECOND, F10 measures that `note_permission_request` has no production
caller. That does not contradict `7ckptx`: R4.4b requires the bound ship DISABLED until detection is proven,
and `PERMISSION_TIMEOUT`'s own docstring already states that `MAX_TURN_TIMEOUT` is consequently the only bound
covering a permission deadlock. So the spec and the code agree, and the gap is a product TODO carried by a
backlog item, not a spec defect.

`7ckptx` remains `- Status: approved` with `- Blocks-Release: next`. This plan does not transition it: A10 is
one of many criteria and `implemented` requires cited evidence for the whole spec, which this plan does not
supply.

No user-facing documentation changes: the deliverable is one new test file.

## Open questions

### OQ-01: Should E-04 keep the isolation-scoped permission-policy contrast, or assert only the bound arming?

- Blocking: no
- Status: resolved
- Owner: plan author (opencode/its_direct-pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED AT AUTHORING: KEEP IT ONLY IF SCRUBBED PER-TEST, AND PREFER OMITTING IT. Recorded rather than left silent because it is the one place this plan declines to restore something the deleted file asserted, and a reviewer should be able to dispute that. THE CASE FOR KEEPING: the contrast is genuinely informative, since A10b's "armed for a NON-isolated turn as well" is only interesting BECAUSE the permission policy is isolation-scoped, and asserting both makes the deliberate difference in scope a measurement rather than a claim. THE CASE AGAINST: that exact assertion is the most-filed flake in this repository's history (F7; `cfgj8s` records twenty-three filings of one non-hermetic assertion), its fix lived inside the file `19313eed` deleted and therefore no longer exists, and it reproduced in THIS authoring lane. A10b does not require it. THE DECISION: E-04 must assert the BOUND arming, which is what the criterion demands and which F7 shows is insensitive to the ambient variable on both hosts. The policy contrast is OPTIONAL; if an executor keeps it, it must `monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)` inside the test and V-04 demands the two-direction proof. A session-wide `conftest.py` scrub is FORBIDDEN either way (`cfgj8s` rejects it by name, citing rolevac `8i0xa7`, where that mechanism made a role guard vacuous), and `conftest.py` is not in `- Scope-Paths:`.

### OQ-02: Does asserting "MAX_TURN_TIMEOUT is the only bound covering a permission deadlock" risk becoming a false assertion once someone wires the detector?

- Blocking: no
- Status: resolved
- Owner: plan author (opencode/its_direct-pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED AT AUTHORING by choosing the assertion's FORM so it survives the wiring. The risk is real: F10's finding is about the CURRENT absence of a caller, and a test that encoded "nothing calls `note_permission_request`" would be a caller-count pin (P16 prohibited) that turns RED the day someone correctly fixes the gap, punishing the right change. So E-07(c) asserts instead that a real wedged child with NO permission observation made is terminated by the max-turn bound, naming `max-turn-timeout` in the record. That is true today and stays true after wiring, because a turn where no ask is observed is still covered only by the coarse bound; it is the same claim in behavioral form. The zero-caller measurement is recorded in the test's DOCSTRING as the dated finding A10c option (ii) asks for, and in F10 here, rather than as an assertion.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: FOR EACH of the two bounds, pasted from an actual run: (a) the child's returncode, which must be NEGATIVE (a signal death; authoring measured `-2`) and NOT `0` and NOT `None`, since a zero would mean the child exited on its own and the bound proved nothing; (b) the measured elapsed seconds, shown to be AT LEAST the bound and comfortably under the `wait` timeout, together with the `check_interval` the test uses (or an explicit statement that it accepts the 1.0 default). REJECT AN ASSERTION THAT ELAPSED IS WITHIN THE BOUND ITSELF: the watch polls at `check_interval` (default 1.0s), so against a 0.3s bound the elapsed time is poll-dominated and legitimately exceeds the bound (review measured 0.475s at the default and 0.382s at `check_interval=0.05`, both firing correctly). A test built on the tighter claim is red at its first run and is the likeliest source of flake under `-n auto` (F12); (c) `watch.fired`, matching the expected constant by NAME; (d) `item["turn_bound_expiry"]["bound"]` and `["disposition"]`, read back off the item, showing the record names the same bound and carries `failed-safely`. PLUS the `TurnBoundWatch` construction QUOTED from the test, shown to pass `reap=lane_containment.bound_expiry_reaper(process, run_dir, item)` with NO inner `reap=` override, which is what makes the kill attributable to the one shared reaper rather than to a double; a test that injects a reaper here does NOT satisfy this item. PLUS, for the permission case, the `assert PERM * 20 <= STALL` line quoted, since A10's "demonstrably not at the coarse no-progress bound" is that margin and a version without it asserts less than the criterion. Confirm the child is a REAL `subprocess.Popen` by quoting the spawn line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: THREE pasted results, each labelled with the construction used. (a) the reset asymmetry in BOTH halves: an EMPTY reap record after `note_permission_request()` + `note_progress()` + a sleep past the permission window, AND a FIRED `max-turn-timeout` despite `note_progress()` being called in a tight loop. Both halves are required; the second is the one that proves the bound is unresettable, which is its entire reason for existing beside the no-progress watchdog, and a version asserting only the first has tested the easy half. (b) an EMPTY reap list for the `is_alive=lambda: False` construction, pasted as an actual empty collection rather than claimed. (c) the `['r']` spy list from the unwritable-run-dir case, PLUS the injected double's signature quoted, shown to keep the `(process, *, run_dir)` keyword shape (a positional-only double raises `TypeError` and would make this item pass for the wrong reason). State explicitly that (c) is the only injected reaper in the file and why.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the six constant values pasted from the live module (`PERMISSION_TIMEOUT`, `MAX_TURN_TIMEOUT`, `HOST_CEILING_OFFSET_SECONDS`, `BOUND_PERMISSION`, `BOUND_MAX_TURN`, `BOUND_EXPIRY_DISPOSITION`), with `MAX_TURN_TIMEOUT` shown equal to `4*60*60` by computation rather than as the literal `14400.0` alone. PLUS the `..._DEADLINE` absence assertions quoted. PLUS `enabled is False` for the both-zero construction AND a shown-empty reap list after entering that watch, since `enabled` returning `False` while a thread still fired would satisfy a property-only check. PLUS how `BOUND_EXPIRY_DISPOSITION` was checked against the shipped terminal vocabulary: name the accessor used, or, if none is importable, say so and show the literal assertion with its comment. PLUS the pasted search over the new file showing zero `inspect.getfile`/`getsource`/`ast.*`/`read_text` uses (required item 5), which this item owns because E-03 is where the temptation to restore the docstring pins lives.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PER HOST, the spy output pasted, showing EXACTLY ONE `TurnBoundWatch` construction per turn and an EQUAL, POSITIVE `max_turn_timeout` for the isolated and non-isolated turns (authoring: oc `14400.0`/`14400.0`, agy `14100.0`/`14100.0`). A count other than one per turn fails this item even if the values match, because A10b's uniformity claim is about one bound being armed on each path. PLUS THE HERMETICITY PROOF IN BOTH DIRECTIONS, which is non-negotiable and is required item 3: the file passing with `OPENCODE_CONFIG_CONTENT` AMBIENT (set it explicitly if absent) and under `env -u OPENCODE_CONFIG_CONTENT`, both summary lines pasted. A pass in one direction only does NOT satisfy this item; that is precisely the historical failure (F7). PLUS, if the policy contrast was kept, the `monkeypatch.delenv` line quoted; if it was omitted, the docstring sentence recording that choice with `cfgj8s` cited. PLUS confirmation that `conftest.py` was NOT modified (`git status --porcelain` pasted).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: per host, the two SHA-256 digests pasted and shown equal, plus the three absence checks (`MAX_TURN_TIMEOUT`, `PERMISSION_TIMEOUT`, `lane-submissions`) each shown `False`. PLUS the docstring sentence quoted, stating that the identity is between two builds AT THE SAME BOUND VALUE and is NOT a claim that changing `MAX_TURN_TIMEOUT` leaves the prompt byte-identical. PLUS a pasted `runner_shared.build_turn_budget_notice` rendering for a nonzero ceiling, demonstrating the value does reach the prompt text (F8); without that rendering the limit is merely described, and the point of stating it is that a later reader not over-read the digest equality. The call takes a STATE DICT (F14), e.g. `build_turn_budget_notice({'options': {'turn_ceiling': 14100.0}})`; a pasted `AttributeError` from passing a float does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: five pasted measurements, each with the exact call: `parse_host_ceiling_seconds(agy_runipd.DEFAULT_TIMEOUT)` -> `14400.0` (and shown NOT to be `240`, since reading `"240m"` as bare seconds is the specific error this guards); `driver_bound_for_host(14400.0)` -> `14100.0` with the strict `<` ordering against the host ceiling shown; the gap shown EQUAL to `HOST_CEILING_OFFSET_SECONDS` (`300.0`); `driver_bound_for_host(None)` -> `14400.0`, unreduced; and `parse_host_ceiling_seconds("banana")` -> `None` with the resulting driver bound shown to be the UNREDUCED default, which is the fail-toward-the-longer-bound direction. PLUS the attribution assertion: a real expiry record pasted whose `bound` is `max-turn-timeout`, so A10d's "a post-mortem can attribute a termination" is demonstrated on a real record rather than on the constant. State explicitly that the "is it documented" half of A10d is NOT asserted here and why (F6).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: TWO PARTS, and the second is this plan's decisive evidence. FIRST, E-07's own assertions: `PERMISSION_TIMEOUT == 0.0`; a DEFAULT-constructed watch with a pending ask noted shown NOT to fire; the docstring recording F10's zero-caller finding with its date and HEAD; and E-07(c) shown to make no `note_permission_request()` call at all (quote the test body), so it asserts the max-turn-only coverage in a form that survives the detector being wired (OQ-02). SECOND, THE MUTATION MATRIX (required item 4, P16's own rule), each cell pasted with the exact mutation used and the resulting pytest line. Mutate via monkeypatch or a throwaway probe, NEVER by editing `agent_workflows/lane_containment.py`; paste `git status --porcelain` afterwards showing no production file touched and no probe left behind. (a) The file under NO mutation: PASSES. (b) With `TurnBoundWatch._expired` stubbed to always return `None` (the bound never notices expiry): E-01's BOTH real-child tests must FAIL, and paste the assertion that tripped in each, which must be the returncode or `fired` assertion and not a timeout in an unrelated place. THE STUB MUST ACCEPT THE `now` ARGUMENT (`lambda self, now: None`), since the loop calls `self._expired(time.monotonic())`; a zero-arg stub raises `TypeError` and would redden the tests for an unrelated reason. Verified achievable at review (F15): the child survives with `rc='TIMEOUT(survived)' fired=None record=None`. (c) With `driver_bound_for_host` stubbed to return `MAX_TURN_TIMEOUT` unconditionally (deleting the host offset): E-06 must FAIL on the ordering or gap assertion, which is what proves that assertion discriminates the offset rather than being true by construction. (d) With `note_progress` stubbed to a no-op: E-02(a)'s FIRST half must FAIL (the permission bound would no longer be disarmed by progress) while its SECOND half still PASSES, and that split result must be shown, because a mutation that reddens both halves has not isolated the resettable/unresettable distinction. CELLS (b), (c) AND (d) ARE THE WHOLE POINT and none may be omitted: without them there is no evidence the restored file can fail when the bounds break, which is the difference between coverage and the appearance of coverage. FINALLY paste the bare-suite summary line (required item 1), `python3 -m pytest tests/test_turn_bounds.py -v` with every test named (item 2), `aw ipd lint --phase pre-transition` conforming (item 6), and `aw sanitize --agent` clean (item 7).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (7 E-items in 3 task groups, under the 18-leaf / 5-group thresholds).

This plan is `- Status: reviewed` with `- Readiness: go-pending-approval` written by `/plan-review`; the author correctly omitted that field, and only the review may set it. Review re-EXECUTED every route at HEAD `f82d7ea53` and the design survives intact (F13); the corrections it applied are one false timing claim (F12: `check_interval` defaults to 1.0s, so E-01 must not assert the wait completes inside the bound's own window) and three bad citations (F9's option count, F10's `git log -S` figure, F11's single baseline), plus the real call shape for `build_turn_budget_notice` (F14). V-07's mutation matrix was verified achievable cell by cell before being demanded of an executor (F15).

EXECUTION CONTRACT. Both open questions are RESOLVED and non-blocking: keep E-04's bound-arming assertion
and treat the policy contrast as optional-if-scrubbed (OQ-01); assert max-turn-only coverage behaviorally
rather than as a caller count (OQ-02). SCOPE FENCE: `- Scope-Paths:` declares `tests/test_turn_bounds.py` and
nothing else; an out-of-scope edit must be genuinely required and then justified to `aw ipd finalize` with a
`--scope-reason` per path.

THE SIX THINGS THIS PLAN MUST NOT DO, each a short path to a change that reads as progress and is not.
FIRST, do NOT read production source in any new test: no `inspect.getsource`/`getsourcelines`/`getfile`, no
`ast.parse`/`walk`/`unparse`, no `read_text()` against an `agent_workflows/` path, and no substring search over
one. That is the backlog item's central constraint and `GUIDING_PRINCIPLES.md` P16's explicit prohibition, and
it is why F5 and F6 record two criterion clauses as human-verified rather than restoring the pins that covered
them. SECOND, do NOT resurrect the deleted `tests/test_turn_bounds.py` wholesale: it is 2417 lines, it carries
the text pins just named, it carries the ambient-env defect F7 shows is live again, and it covers criteria
outside this item. Write the new file from the measured routes in Findings. THIRD, do NOT wire
`note_permission_request` into either driver (F10); file the carrier instead, and record its id6 in Deferred
before finalize. FOURTH, do NOT add a session-wide `OPENCODE_CONFIG_CONTENT` scrub to `conftest.py`: backlog
`cfgj8s` rejects that mechanism by name, and `conftest.py` is not in scope. FIFTH, do NOT substitute a fake
process for E-01's real child, and do NOT inject a `reap=` double there: the criterion is that a REAL process
is terminated through the ONE shared reaper, and both shortcuts would make the test pass while proving
something weaker. SIXTH, do NOT add a CLI flag or config key for either bound while in the area (F9 shows the
surface is clean; A10e is out of scope).

THE HARD-MUST HONESTY RULE: paste the ACTUAL command output for every `V-*`. V-01 requires a real negative
returncode, not a claim that the child was killed; V-04 requires the hermeticity proof in BOTH ambient
directions, since a one-direction pass is exactly the historical flake; and V-07 requires the mutation matrix
in all four cells, since an all-green file proves nothing about sensitivity. If any measurement contradicts
this plan's authoring baseline, revise the plan's reasoning and say so rather than restating the baseline.

Commit path-scoped through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Before every commit
run `git diff --cached --name-only` and unstage anything that is not yours. LIFECYCLE TRANSITION: reaching
`.aw/records/plans/executed/` via `aw ipd finalize` is unconditionally owed, but its OWNER is conditional:
under `aw oc run` / `aw agy run` the RUNNER owns that transition, so do not invoke `aw ipd finalize` yourself
in a runner-driven execution; a HAND execution invokes it. Never hand-roll a `git mv` to `executed/`. Do not
claim done until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence.
