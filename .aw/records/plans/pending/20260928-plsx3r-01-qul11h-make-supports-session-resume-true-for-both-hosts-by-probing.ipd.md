# IPD: Make supports_session_resume true for both hosts by probing each host's own resume argv, and delete the host-identity assertion

- Date: 2026-09-28
- Kind: child
- Concern: `host_sandbox_profile.detect_host_capabilities` sets `supports_session_resume = True` inside an `if host == "opencode":` branch, and that is FALSE AS A DESCRIPTION: Antigravity demonstrably resumes a conversation, and the repository already has a shipped test proving it (`tests/test_defect_report.py::HostResumeSpellingTests::test_antigravity_resumes_with_conversation` asserts `--conversation <id>` in `agy_runipd.run_agy_turn`'s real argv). Re-measured at HEAD `e0717990`: `aw host capabilities antigravity` prints `NO   supports_session_resume` while `aw host capabilities opencode` prints `yes`, so the shipped operator-facing report tells an operator that agy cannot do a thing agy does on every resumed turn. The field also GATES NOTHING (`ACTION_CAPABILITY_REQUIREMENTS` has one row, `read_only`, whose `required` is `()`), which is why the lie has survived. The combination is the live trap the backlog item names: plan `b7xarm` added a same-session re-ask BOTH hosts perform, wiring it to this field would have been the natural-looking move and would have WRONGLY REFUSED agy, and that plan had to carry an explicit written prohibition (its E-05: "DO NOT ADD A CAPABILITY GATE FOR THIS") plus a finding (F-18) instead of a fix, because `host_sandbox_profile.py` was not in its `Scope-Paths`. Worse than the wrong value is HOW it is decided: the assignment is the module's own self-documented anti-pattern, an assertion from HOST IDENTITY rather than from an executed attempt, called out by name in review `mjx7ne` PR-007 ("contradicting the attempt-not-inspect discipline its own docstring publishes") and left unfixed there for the same scope reason. This plan is the first one authorized to touch the file.
- Scope: IN: add an EXECUTED probe (`_probe_session_resume`) that derives the verdict from each host's REAL argv builder (`oc_runipd.run_opencode` -> `--session <id>`, `agy_runipd.run_agy_turn` -> `--conversation <id>`) by capturing the argv at the `subprocess.Popen` seam and refusing to launch, then asserting the sentinel session id is carried; wire it as a per-host probe so `detect_host_capabilities` sets the field from that verdict for BOTH runner hosts and for NO other host; DELETE the `supports_session_resume = True` line from the `if host == "opencode":` identity branch; record the verdict's evidence in `probe_notes` like every other probe; add tests pinning the true/true/false verdict triple and pinning that the value tracks the ARGV rather than a table. OUT, and each for a stated reason: `emits_structured_tool_events`, the OTHER capability that same identity branch asserts (a real defect, filed as its own backlog item by E-07, because probing a host's event-stream shape is a different mechanism from reading one argv list and merging them would make a single plan own two probes); adding any `ACTION_CAPABILITY_REQUIREMENTS` row or otherwise making the field GATE anything (that reverses maintainer ruling `4h7tt0` OQ-02 and belongs with the live carriers `b7tlsh`/`oq05nc`); DELETING the field instead of fixing it (rejected on evidence, see F-06 and OQ-01); calling the preflight from a runner (pending plan `iot7hc` owns that, and this plan must not race it); and `host_capability_registry.py`, a different concern with its own TTL/evidence model.
- Scope-Paths: agent_workflows/host_sandbox_profile.py, tests/test_host_sandbox_profile.py, tests/test_host_capability_extension.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: plsx3r
- Blocks-Release: next
- Set: plsx3r
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: qul11h

## Workflow history

- 2026-09-28 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `plsx3r`. Re-measured every claim at HEAD `e0717990` and resolved the item's open "either set it TRUE for antigravity, or delete the field" choice AGAINST deletion, on three pieces of repository evidence recorded as F-06 (spec `25kzda` 5.2 requires the descriptor to answer "create/resume an executor session" independently per host; the sibling `supports_deny_push` deletion precedent in `01reg8` turned on the flag being UNSHIPPED AND UNWANTED whereas this capability is shipped, wanted and exercised; and `le9q02`'s host-dedup analysis classifies session resume as a "Genuine Host Capability" appropriately owned by this module). Also measured the design constraint the item does not state and which decides the probe's shape: `oc_runipd` imports `host_sandbox_profile` AT MODULE LEVEL, so the probe MUST use a function-local import or it creates a cycle (F-04); and a naive in-process probe re-enters `detect_host_capabilities` one level deep through `_apply_execution_profile` (F-05), which is why E-02 prescribes a re-entrancy guard and E-03 pins it with a test.
- 2026-09-28 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `supports_session_resume` TRUE for both runner hosts and decided by an EXECUTED probe of each host's own resume argv, so the shipped capability report stops asserting that Antigravity cannot resume a conversation it resumes on every resumed turn, and so the next author who reaches for this field to gate a both-hosts behavior gets a correct answer instead of a written prohibition.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline the lie, then pin it with a test that fails first

- [ ] E-01 RE-MEASURE the premise and write the result into the plan as an execution note, because every load-bearing fact here is dated and each has a cheap check. Record, with the HEAD they were taken at: (a) the operator-facing lie, `python3 -m agent_workflows host capabilities opencode` and `... antigravity`, showing `yes` and `NO` respectively on the `supports_session_resume` row; (b) the identity branch itself, `rg -n "supports_session_resume|emits_structured_tool_events" agent_workflows/host_sandbox_profile.py`, showing the field declared once and assigned once inside `if host == "opencode":`; (c) that the field gates nothing, `python3 -c "from agent_workflows import host_sandbox_profile as h; print(h.ACTION_CLASSES, {a: r.required for a, r in h.ACTION_CAPABILITY_REQUIREMENTS.items()})"`; (d) that BOTH hosts really do resume, by running the SHIPPED proof `python3 -m pytest tests/test_defect_report.py::HostResumeSpellingTests -o addopts="" -v`. IF ANY HAS MOVED, SAY SO AND RE-SCOPE rather than proceeding: in particular, if some action has acquired a non-empty `required` tuple that names this field, then the change is no longer cosmetic-to-runtime and the risk assessment in the gate must be redone before editing. Trust the tree, not this plan's Concern.
  - Depends on: none
  - Expected outcome: a written, symbol-cited baseline showing the two-host asymmetry in the shipped report, the single identity-branch assignment, `ACTION_CLASSES == ('read_only',)` with `read_only` requiring nothing, and `HostResumeSpellingTests` passing (2 tests) so the "agy resumes" premise is proven by the repository rather than asserted by this plan.
  - Execution state: pending

- [ ] E-02 WRITE THE FAILING TEST FIRST, appending a `SessionResumeProbeTests` class to `tests/test_host_sandbox_profile.py` (the file that owns `CONTRACT_FIELDS` and every `detect_host_capabilities` assertion), so the defect is pinned by something that fails BEFORE the fix and passes after. Three cases, and the FIRST is the one that must fail: (1) `detect_host_capabilities("antigravity").supports_session_resume` is True; (2) `detect_host_capabilities("opencode").supports_session_resume` is True; (3) a host that is NEITHER runner, `detect_host_capabilities("scripted").supports_session_resume`, is False, which is the fail-closed half and must not be dropped, because a probe that returns True for everything asserts a capability for a host with no argv builder at all. ALSO assert the field's note lands in `probe_notes`, matching the shipped rule that "every runner-safety verdict must publish its evidence" (`tests/test_host_capability_extension.py` asserts exactly this for the runner-safety pair). DO NOT assert on `sys.platform`-dependent state: `supports_fresh_verifier_session` is True on linux and False on darwin/win32 (measured), and the probe this plan adds must be platform-INDEPENDENT for the same reason `probe_runner_safety_capabilities` is applied before the sandbox platform gate; if the executor finds the new verdict changing with the asked-about platform, that is a defect in E-04's placement, not a test to relax.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_host_sandbox_profile.py -k SessionResumeProbeTests -o addopts="" -v` FAILS on case (1) with an assertion message (not a collection or import error), and the failure output is pasted into V-02 as the before-state.
  - Execution state: pending

### Task group 2: the executed probe, and deleting the identity assertion

- [ ] E-03 ADD THE PROBE `_probe_session_resume(host) -> Tuple[bool, str]` to `agent_workflows/host_sandbox_profile.py`, returning the `(supported, note)` pair every probe in this module returns, and hold it to the module's OWN standard rather than a weaker one. WHAT IT MUST ATTEMPT: build the host's REAL turn argv through the host's REAL argv builder with an explicit sentinel session id, capture the argv at the `subprocess.Popen` seam, REFUSE TO LAUNCH, and return True only if the captured argv carries that host's resume flag IMMEDIATELY FOLLOWED BY the sentinel. The two spellings are DATA in the probe, one row per host, not an `if`: `{"opencode": ("--session", <oc invoker>), "antigravity": ("--conversation", <agy invoker>)}`; an unknown host returns `(False, ...)` with the reason recorded, exactly as `_RUNNER_SAFETY_PROBES` returns not-supported for a capability with no probe. WHY THE FLAG PRESENCE IS NOT ENOUGH AND THE SENTINEL IS REQUIRED: `--session` with a stale or empty value resumes nothing, and `agy_runipd.run_agy_turn` has a `--continue` FALLBACK it takes when no id is supplied, so a flag-only criterion would report True for a host that silently started a fresh conversation. This is the same distinction `_probe_bwrap`'s docstring records as a regression found at verification ("the launcher started" is not evidence of enforcement). USE A FUNCTION-LOCAL IMPORT of the two runner modules, MANDATORY and not stylistic: `oc_runipd` imports THIS MODULE at module level (`from agent_workflows.host_sandbox_profile import ... detect_host_capabilities ...`), so a module-level import here is an import cycle (F-04). ANY exception, missing symbol, unexpected argv or timeout yields `(False, <reason>)` and never propagates, per `probe_runner_safety_capabilities`' own rule that "a probe must never propagate; unknown => False". RESTORE `subprocess.Popen` IN A `finally`, for the process-global reason `forced_runner_safety_verdicts` exists: a probe that swapped it and then raised would break every later subprocess in the interpreter.
  - Depends on: E-02
  - Expected outcome: a scratch run shows `_probe_session_resume("opencode")` and `("antigravity")` each return `(True, <note naming the observed flag and sentinel>)`, `("scripted")` returns `(False, <note saying no argv builder is known for that host>)`, and no real host process was spawned (the probe's own note, or a spy, shows the launch was refused before exec).
  - Execution state: pending

- [ ] E-04 WIRE THE VERDICT AND DELETE THE IDENTITY ASSERTION, in `detect_host_capabilities`. Two edits, and the deletion is the point of the plan: (a) set `supports_session_resume` from `_probe_session_resume(host)` and record its note in `probe_notes["supports_session_resume"]`; (b) DELETE the `caps.supports_session_resume = True` line from the `if host == "opencode":` branch, leaving that branch with `emits_structured_tool_events` alone (E-07 files the remaining half rather than fixing it here). PLACE THE CALL WHERE THE PLATFORM GATE CANNOT SWALLOW IT: alongside `probe_runner_safety_capabilities`, BEFORE the `if not plat.startswith(CERTIFIED_PLATFORM): return caps` early return, because resuming a session is not a sandbox rung and a Linux-only verdict would make the report claim on macOS that neither host can resume. GUARD RE-ENTRANCY WITH A MODULE-LEVEL FLAG, and know the measured reason rather than treating it as defensive noise: `oc_runipd.run_opencode` calls `_apply_execution_profile`, which itself calls `detect_host_capabilities("opencode")`, so driving the real argv builder from inside this function re-enters it. MEASURED in a scratch harness: nesting reaches depth 2 and then TERMINATES, because the inner call's probe is what would recurse and the guard stops it; without a guard the nesting is unbounded in principle and, worse, every real resumed turn would pay the probe twice. When the guard is set, return the CONSERVATIVE `(False, "re-entrant probe suppressed")` rather than an optimistic True: an unprobed capability claims nothing (the dataclass docstring's rule). HONOR THE EXISTING `platform_name` CONTRACT: `detect_host_capabilities` already refuses to decide runner-safety capabilities when asked about a platform it is not running on, and this verdict is platform-independent (it reads an argv list), so it is decided unconditionally; state that difference in a comment so a later reader does not "restore parity" by moving it inside the `plat == running_platform` block and thereby make the field False on every cross-platform query.
  - Depends on: E-03
  - Expected outcome: `rg -n "supports_session_resume" agent_workflows/host_sandbox_profile.py` shows the field declared, probed and noted, with NO assignment inside `if host == "opencode":`; E-02's three cases all PASS; and `python3 -m agent_workflows host capabilities antigravity` prints `yes  supports_session_resume` with a `why:` line naming the observed `--conversation` flag.
  - Execution state: pending

### Task group 3: pin the anti-regression, keep the report honest, file the sibling

- [ ] E-05 PIN THAT THE VERDICT TRACKS THE ARGV AND NOT A TABLE, with one test in `tests/test_host_capability_extension.py` (the file that owns the contract's presence-versus-observation table and its `PRESENCE_VS_OBSERVATION` anti-inference rows). This is the test the backlog item asks for in its own words: "it needs a test that asserts the value against each host's real argv rather than against a hand-maintained table." The shape: monkeypatch the ARGV BUILDER the probe drives so it emits an argv WITHOUT the resume flag (or with the flag carrying a different id), restore it in a `finally`, and assert the verdict flips to False. WHY THIS IS THE LOAD-BEARING TEST: E-02's three cases would pass just as green against a hand-written `{"opencode": True, "antigravity": True}` dict, which is the SAME class of defect this plan is fixing, one row wider. Only a test that breaks the argv and sees the verdict move proves an observation is happening. Do NOT weaken this into asserting the probe function was called: a called function that returns a constant is exactly the fail-open case.
  - Depends on: E-04
  - Expected outcome: with the argv builder patched to omit the resume flag the verdict is False and with it restored the verdict is True, both in one test, and a deliberate scratch experiment confirms the test FAILS if the probe body is replaced by `return True, "table says so"`.
  - Execution state: pending

- [ ] E-06 CORRECT THE PROSE THIS PLAN FALSIFIES, and nothing else. Two claims inside `host_sandbox_profile.py` become false the moment E-04 lands, and both are warnings a later reader will rely on: the `if host == "opencode":` branch comment "Proven by the existing driver: `--format json` streams structured events and `--session <id>` resumes an exact session (oc_runipd.run_opencode)", which after the deletion must describe only the event-stream half it still covers; and any surviving sentence implying the contract's booleans are all decided before the platform gate or all decided by probe-or-declaration, which E-04's new placement widens. ALSO add the probe to the module docstring's list of what is decided by attempt, because that docstring is the published guarantee and a probe absent from it is invisible to an auditor. DO NOT rewrite review `mjx7ne`'s recorded finding or the executed plans that cite this line: those are history, and the execution contract forbids changing what an executed plan records. DO NOT touch `tests/test_defect_report.py`: its two argv assertions are this plan's evidence base and must pass UNCHANGED, which is the point of leaving them out of `Scope-Paths`.
  - Depends on: E-05
  - Expected outcome: no sentence in `host_sandbox_profile.py` still attributes `supports_session_resume` to host identity or to the OpenCode driver alone; the module docstring names the new probe among the executed ones; `git status --short tests/test_defect_report.py` shows no change.
  - Execution state: pending

- [ ] E-07 CONFIRM THE DEFERRED ROW'S CARRIER IS REAL, LIVE AND STILL ACCURATE. Backlog item `42da1n` was filed AT AUTHORING rather than deferred to execution, so this item mints nothing; it confirms the carrier the Deferred section names is the thing a reader of that row relies on. Check and record: (a) the item resolves and is still live, `python3 -m agent_workflows find backlog 42da1n` (or read `.aw/records/backlog/open/`), showing `- Status: open`, `- Work-Kind: bug` and `- Blocks-Release: next`; (b) its central factual claim still holds, `rg -n "emits_structured_tool_events" agent_workflows/host_sandbox_profile.py`, showing that field STILL assigned inside the `if host == "opencode":` branch after E-04 removed only its sibling, because if E-04 removed this one too that is over-scope to be reverted rather than accepted; (c) the repository gate is clean, `python3 -m agent_workflows check release-gates`. IF THE ITEM IS GONE OR ALREADY `done`, do NOT silently proceed: the Deferred row's carrier is then dangling, so re-point it and say so.
  - Depends on: E-06
  - Expected outcome: `42da1n` confirmed `open` / `bug` / `Blocks-Release: next`, `emits_structured_tool_events` confirmed still assigned in the identity branch (this plan deliberately left it), and `check release-gates` clean.
  - Execution state: pending

- [ ] E-08 RUN THE BARE SUITE, `python3 -m pytest`, and compare against a baseline taken the same way BEFORE any edit in this plan. Bare is required: `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so `-n0` makes this suite several times slower here and a second `-q` suppresses the `N passed` summary line this plan must paste.
  - Depends on: E-07
  - Expected outcome: no new failures relative to the same-day baseline, with BOTH summary lines captured.
  - Execution state: pending

## Project conventions discovered (Step 0)

- PRESENCE-BASED AND IDENTITY-BASED INFERENCE ARE FORBIDDEN IN THIS MODULE, in writing, with a measured justification: the docstring's "WHY THE PROBE EXECUTES INSTEAD OF INSPECTING" records that on the development host every signal said "sandbox available" while `unshare -Umr true` failed with `Operation not permitted`, so an inspecting probe would have granted hard mode to a host that could not enforce it. The line this plan deletes is that same anti-pattern, and review `mjx7ne` PR-007 already named it as such.
- A PROBE MUST PROVE THE THING, NOT THE ATTEMPT'S SUCCESS. `_probe_bwrap`'s docstring records the regression found at verification: returning True because `bwrap ... true` exited 0 proves the launcher started, not that the partition is enforced. This is why E-03 requires the sentinel id in the argv rather than the flag's mere presence.
- A PROBE NEVER PROPAGATES. `probe_runner_safety_capabilities` catches `Exception` and maps it to `(False, "probe raised ...")`; `_run_probe` maps every `OSError`/`SubprocessError` including `TimeoutExpired` to a nonzero result. Unknown means not-supported.
- EVERY VERDICT PUBLISHES ITS EVIDENCE in `probe_notes`, and a test enforces it for the runner-safety pair ("every runner-safety verdict must publish its evidence").
- THE CONTRACT'S FIELD LIST IS A LITERAL TUPLE IN THE TESTS, not dataclass introspection: `tests/test_host_sandbox_profile.CONTRACT_FIELDS` drives the default-False and snapshot assertions, and `host_cmd._capability_rows`' docstring records that this is "exactly how three fields once became structurally invisible to a guarantee that appeared to cover them". `supports_session_resume` is already in that tuple, so this plan adds no field and removes none.
- A PROCESS-GLOBAL SEAM MUST BE RESTORED IN A `finally`, because the suite runs order-randomized (`pyproject.toml` `addopts` carries `-p randomly` behavior via its configured plugins) and a leaked global is an order-dependent failure. `forced_runner_safety_verdicts` exists for exactly this and is the shape E-03's `Popen` swap and E-05's argv patch must copy.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `e0717990` (2026-09-28) unless stated otherwise.

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | THE LIE IS OPERATOR-FACING, not merely internal. | `python3 -m agent_workflows host capabilities antigravity` prints `NO   supports_session_resume`; the same verb for `opencode` prints `yes`. Both rows come from `host_cmd._capability_rows`, which introspects the dataclass. | The defect is visible in a shipped read-only verb an operator is told to run, which is what makes it a `bug` rather than a `chore`. V-04 requires the corrected output pasted. |
| F-02 | AGY REALLY DOES RESUME, and the repository already proves it, so this plan need not establish the premise. | `tests/test_defect_report.py::HostResumeSpellingTests` has two tests: `test_opencode_resumes_with_session` (asserts `--session` then the id) and `test_antigravity_resumes_with_conversation` (asserts `--conversation` then the id, and asserts `--session` is ABSENT). Both pass. `agy_runipd.run_agy_turn` emits `--conversation <id>` with `--continue` as its no-id fallback. | E-01d runs that shipped test as the baseline, and E-03's probe reuses its exact capture technique (swap `subprocess.Popen`, record argv, refuse to launch) rather than inventing a second one. |
| F-03 | THE FIELD GATES NOTHING TODAY, so this change is report-and-trap-correctness, not a behavior change. | `ACTION_CLASSES == ('read_only',)`; `ACTION_CAPABILITY_REQUIREMENTS['read_only'].required == ()`. No `.required` tuple anywhere names this field. `rg` finds no reader of the field outside `host_sandbox_profile.py` itself, `host_cmd`'s introspecting report, and tests. | The gate's risk statement can honestly say no run changes behavior. It ALSO means the tests in E-02/E-05 are the only thing that will ever notice a regression, which raises rather than lowers the bar on E-05. |
| F-04 | A MODULE-LEVEL IMPORT OF EITHER RUNNER FROM THIS MODULE IS AN IMPORT CYCLE. | `oc_runipd` imports this module at module level: `from agent_workflows.host_sandbox_profile import SandboxProfileError, build_sandbox_plan, detect_host_capabilities, enter_sandbox, select_execution_profile`. Verified that a FUNCTION-LOCAL `from agent_workflows import oc_runipd` inside this module works in both import orders. | E-03 mandates the function-local import and says why. An executor who "tidies" it to the top of the file breaks the package. |
| F-05 | A NAIVE IN-PROCESS PROBE RE-ENTERS `detect_host_capabilities`, because the argv builder itself asks for capabilities. | `oc_runipd.run_opencode` calls `_apply_execution_profile`, which calls `detect_host_capabilities("opencode")`; instrumenting the real function showed exactly one such call per `run_opencode`. A scratch harness that wired the naive probe in reached nested depth 2 and terminated. | E-04 requires a re-entrancy guard returning the CONSERVATIVE False, and E-04's expected outcome plus V-04 make the guard observable. Without it every resumed turn pays the probe twice. |
| F-06 | THE ITEM'S OPEN CHOICE ("set it TRUE for antigravity, or delete the field") RESOLVES AGAINST DELETION, on three independent pieces of evidence. | (i) Spec `25kzda` 5.2's descriptor list requires the host answer, independently, whether it can "create/resume an executor session and create a genuinely fresh verifier session", so deleting the field would delete a spec-required answer. (ii) The DELETION PRECEDENT does not transfer: `01reg8` removed `supports_deny_push` because it was UNSHIPPED (added `30108f78`, newest tag `v1.3.0-rc.1`) and named enforcement that does not exist; session resume is shipped, exercised on every resumed turn, and proven by a passing test. (iii) `le9q02`'s host-dedup analysis classifies `supports_session_resume` under "Genuine Host Capability ... appropriately owned by `host_sandbox_profile.HostSandboxCapabilities` via executed probes rather than passive label strings in `HostLabels`". | The plan FIXES the field. OQ-01 records the rejected alternative and the evidence, so a reviewer can overrule it cheaply rather than re-deriving it. |
| F-07 | THE SAME IDENTITY BRANCH TELLS A SECOND LIE, and that one is CONSUMED, which is why it must not be fixed here. | The branch sets `emits_structured_tool_events = True` for opencode only, yet `agy_runipd.run_agy_turn` passes `--output-format stream-json` and the module parses those events. Unlike session resume, this field IS read: `run_discovery_then_execution` refuses to claim a before-edit barrier unless `supports_read_only_phase AND emits_structured_tool_events`, and `tests/test_host_sandbox_profile.py` constructs descriptors with `emits_structured_tool_events=True` for that path. | E-07 FILES it rather than fixing it: flipping it changes a barrier decision, which is a behavior change this plan's gate explicitly disclaims. Carried in Deferred. |
| F-08 | A PENDING PLAN TOUCHES THE ADJACENT MACHINERY, so the two must not collide. | `.aw/records/plans/pending/20260928-7bj5sa-01-iot7hc-...ipd.md` wires `preflight_host_capabilities` into `runner_shared.execute_item_core`. Its `Scope-Paths` are `runner_shared.py`, `run_selection_policy.py` and a new test file; it does NOT name `host_sandbox_profile.py`, and its OQ-02 explicitly asks whether it may edit that file's docstring. | NO path overlap, so the two can run in either order. But if `iot7hc` executes FIRST and its OQ-02 is resolved as "amend", the docstring E-06 edits will already have moved; the executor must re-read the docstring immediately before editing rather than applying a remembered diff. |
| F-09 | THE COST IS REAL BUT SMALL, and worth stating because the probe runs inside a shipped read-only verb. | Measured: driving one host's real argv builder in-process takes 46 ms (opencode) and 22 ms (antigravity) cold, including a `git init` in a temp dir; a warm `detect_host_capabilities` is 0.3 ms today. As a subprocess the same probe is ~300 ms per host. | E-03 runs IN-PROCESS, not as a subprocess: ~70 ms for both hosts is acceptable for `aw host capabilities`, ~600 ms is not. If the executor finds a reason a subprocess is unavoidable, that is a re-scope, not a silent substitution. |

## Proposed changes (ordered, validatable)

1. Baseline the two-host asymmetry, the identity branch and the shipped "agy resumes" proof (E-01).
2. Pin the defect with a three-case test that fails on the antigravity case first (E-02).
3. Add the executed argv probe, sentinel-checked, function-local import, never propagating (E-03).
4. Wire the verdict before the platform gate, guard re-entrancy, and DELETE the identity assignment (E-04).
5. Pin that the verdict tracks the argv and not a table, which is the test the backlog item asked for (E-05).
6. Correct only the prose this change falsifies, and add the probe to the published guarantee (E-06).
7. Confirm the Deferred row's carrier `42da1n` is live and its claim still true (E-07).
8. Bare suite, before and after (E-08).

## Deferred / out of scope (with reason)

- FIXING `emits_structured_tool_events`, the other half of the same identity branch (F-07). Deferred because it is CONSUMED by `run_discovery_then_execution`'s barrier decision, so flipping it changes behavior, and because probing a host's event-stream shape is a different mechanism from reading one argv list. FILED AT AUTHORING rather than promised to the executor, so the carrier below names a real item that exists now; E-07's only remaining job is to VERIFY it rather than to mint it.
  - Carrier: 42da1n
- MAKING THIS FIELD GATE ANY ACTION. Adding a `required` entry naming it would give the corrected capability teeth, and it is deliberately not here: it reverses maintainer ruling `4h7tt0` OQ-02 (executed by `01reg8`) that removed action verdicts precisely because nothing consumed them, and it needs a spec-level answer about what each action must prove.
  - Carrier: b7tlsh
- BUILDING THE MISSING ENFORCEMENT the descriptor's other unproven capabilities name (`supports_commit_gateway`, and a real push-denial boundary). Out of scope by size and by subject; this plan corrects a DESCRIPTION, it does not build a boundary.
  - Carrier: oq05nc
- CALLING THE PREFLIGHT FROM A RUNNER. Pending plan `iot7hc` owns that work and declares `runner_shared.py`; this plan must not race it (F-08).
  - Carrier-Declined: Nothing is owed. This row is a scope fence rather than a dropped obligation: the work exists, is already designed, and is already owned by a pending plan, so no successor must discover it. Naming a carrier here would duplicate a live plan as if it were an untracked gap.
- `host_capability_registry.py`, with its `unverified`/TTL/evidence-digest model. A different concern that this plan neither needs nor degrades; `mjx7ne` kept it out for the same reason.
  - Carrier-Declined: Nothing is owed. Excluding an unrelated module creates no gap; the row exists only because a reader might expect a capability change to touch every file with "capability" in its name.
- AMENDING SPEC `25kzda`. Its 5.2 descriptor list already REQUIRES the host to answer whether it can resume an executor session; this plan makes the shipped answer correct rather than changing what the spec requires, so `Scope-Paths` names no `.spec.md` file, which is the declaration both runners announce at run start.
  - Carrier-Declined: Nothing is owed. The spec and the code AGREE after this change and disagreed before it, so there is no divergence for a successor to reconcile. The one live spec question in this area (whether 5.2 should claim commit-gateway enforcement at all) is carried by `b7tlsh` above and is not duplicated here.

## Scope check

- Over-scope: none. `host_sandbox_profile.py` carries E-03/E-04/E-06, `tests/test_host_sandbox_profile.py` carries E-02, `tests/test_host_capability_extension.py` carries E-05, and E-01/E-07 write no tracked file except the new backlog item E-07 mints (which is the artifact it is instructed to create, filed through `aw backlog new`).
- Under-scope, DELIBERATE and stated plainly: after this plan the field is CORRECT and still gates nothing (F-03). An operator reading "the session-resume capability was fixed" must not conclude a protection was added; what was fixed is a description and a trap. The sibling `emits_structured_tool_events` also remains wrong until E-07's item is worked.
- `tests/test_defect_report.py` is deliberately NOT in `Scope-Paths`: its two argv assertions are this plan's evidence base, and they must pass unchanged. If the executor finds them failing, the probe has altered a host's argv, which is a defect in E-03 and not a test to update.
- The pending plan `iot7hc` shares no path with this one (F-08), so no ordering constraint is declared. The executor must still re-read `detect_host_capabilities` and the module docstring immediately before editing, because a concurrent worker may have moved them.

## Required tests / validation

- The new `SessionResumeProbeTests` in `tests/test_host_sandbox_profile.py` must pass, with case (1) having been OBSERVED FAILING before E-04 and that failure pasted into V-02.
- The new argv-tracking test in `tests/test_host_capability_extension.py` must pass, and must be shown to FAIL against a constant-returning probe body (V-05).
- `tests/test_defect_report.py` must pass UNCHANGED (it is not in `Scope-Paths`), since it is the independent proof that both hosts resume.
- `python3 -m agent_workflows host capabilities opencode` and `... antigravity` must both print `yes  supports_session_resume` with a `why:` note naming the observed flag.
- The bare suite `python3 -m pytest`, before and after, with both summary lines pasted.

## Spec / documentation sync

- No spec amendment, and the reason is substantive rather than procedural: spec `25kzda` 5.2's descriptor list already requires the host to answer, independently, whether it can "create/resume an executor session", and its paragraph on the shipped contract describes a 12-field dataclass. This plan changes neither the field count nor the requirement; it makes the shipped ANSWER true. `Scope-Paths` therefore names no `.spec.md` file.
- `host_sandbox_profile.py`'s module docstring IS the published guarantee for this contract, and E-06 updates it in the same change that changes what is probed, so the tree never carries a guarantee this plan falsified.
- No `docs/` page or `CHANGELOG.md` entry mentions this capability (measured: `rg "session_resume|session resume" docs/ CHANGELOG.md README.md` is empty), so no user-facing documentation changes.

## Open questions

### OQ-01: Should the field be FIXED (probed, true for both hosts) or DELETED, as the backlog item leaves open?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED AT AUTHORING FROM REPOSITORY EVIDENCE, not deferred to the executor or to the maintainer: FIX IT. Three pieces of repository evidence, recorded as F-06, point the same way. Spec `25kzda` 5.2 requires the descriptor to answer whether a host can resume an executor session, so deleting the field deletes a spec-required answer and would need a spec amendment this plan declines to make. The apparent precedent for deletion does not transfer: `01reg8` removed `supports_deny_push` because it was unshipped and named enforcement that does not exist, whereas session resume is shipped, exercised on every resumed turn, and already proven by a passing test. And `le9q02`'s host-dedup analysis independently classifies session resume as a genuine host capability belonging to this module's probed contract rather than to passive label data. Non-blocking because the fix is strictly better than the status quo under EITHER answer: a probed, correct, ungated field is not an obstacle to a later decision to delete it, whereas the current state actively misleads. THE HONEST COST OF THE DEFAULT: the repository keeps a field that gates nothing, which is half of what the backlog item complains about, and F-03 says so plainly. If the maintainer prefers deletion, that is a different plan with a spec amendment in its `Scope-Paths`, and this one should be superseded rather than edited.

### OQ-02: Should the probe run in-process (~70 ms for both hosts) or as an isolated subprocess (~600 ms), given this module's other probes use subprocesses?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Carrier-Declined: This question is answered INSIDE this plan under either outcome and leaves no work behind it. Under the default the in-process probe is what E-03 builds and V-03 verifies; under the alternative the executor substitutes a subprocess in the same E-item and V-03's evidence changes shape but not existence. There is no obligation a successor would inherit either way, so a carrier would name work that does not exist.
- Resolution or deferral rationale: DEFAULT: IN-PROCESS. The subprocess pattern in this module exists for a specific reason that does not apply here: a sandbox rung must be attempted in a process that can be KILLED and whose kernel-level denial cannot be faked, so `_probe_landlock` and `_probe_bwrap` spawn. This probe reads an argv LIST from a pure builder and never launches anything, which is the same in-process shape `_probe_fresh_verifier_session` already uses. MEASURED cost (F-09): 46 ms + 22 ms in-process versus ~300 ms per host as a subprocess, paid inside the shipped read-only verb `aw host capabilities`; the subprocess form is roughly an order of magnitude worse for no isolation this probe needs. Non-blocking because both forms produce the same verdict and the tests in E-02/E-05 are indifferent to which is used. THE RISK THE DEFAULT ACCEPTS, stated so a reviewer can weigh it: an in-process probe swaps the process-global `subprocess.Popen` for the duration of the capture, so a bug in its `finally` would break every later subprocess in the interpreter. E-03 mandates the `finally` for exactly this reason, and it is the one thing a reviewer should check hardest in the diff.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted output of all four baseline commands with the HEAD they were run at, specifically including both `host capabilities` runs side by side so the `yes`/`NO` asymmetry is visible in one place, and the `HostResumeSpellingTests -v` run showing 2 passed with both test names. If any fact moved, the paste must be accompanied by the explicit re-scope statement E-01 demands.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted FAILING run of `python3 -m pytest tests/test_host_sandbox_profile.py -k SessionResumeProbeTests -o addopts="" -v` taken BEFORE E-04, showing the antigravity case failing on an ASSERTION (a collection error, import error, or skip is not acceptable evidence) and showing the opencode and scripted cases' outcomes. A test that passed on its first run is not evidence of a pinned defect and must be rejected here.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the probe function quoted from the file, plus a pasted scratch run of `_probe_session_resume` for `opencode`, `antigravity` and `scripted` showing the three `(bool, note)` pairs, with each True note naming the flag AND the sentinel it observed. Also paste evidence that NO host process was launched (for example the note's own wording plus a spy or `Popen` counter showing the launch was refused), and quote the `finally` that restores `subprocess.Popen`, since OQ-02 records that as the highest-risk line in the diff.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: (a) `rg -n "supports_session_resume" agent_workflows/host_sandbox_profile.py` showing no assignment inside the `if host == "opencode":` branch; (b) the now-PASSING `SessionResumeProbeTests` run; (c) the pasted `python3 -m agent_workflows host capabilities antigravity` output showing `yes  supports_session_resume` with its `why:` line; (d) the pasted output of the SAME verb for a NON-Linux platform query (for example `python3 -c "from agent_workflows import host_sandbox_profile as h; print(h.detect_host_capabilities('antigravity','darwin').supports_session_resume)"`) printing `True`, which is what proves the verdict was placed before the platform gate rather than inside it; and (e) evidence the re-entrancy guard fires, by driving the real argv builder once and showing the probe was not entered recursively.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the pasted PASSING run of the new argv-tracking test, AND the pasted FAILING run of that same test against a deliberately sabotaged probe body (`return True, "table says so"`), restored afterwards. The second half is the whole point: a test that cannot distinguish an observation from a hardcoded table would reproduce this plan's own defect, and only the sabotage run proves it can.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the corrected branch comment and the module docstring's probe list both quoted in full, so a reviewer can confirm no sentence still attributes `supports_session_resume` to host identity; plus `git status --short tests/test_defect_report.py` showing no change and a pasted `python3 -m pytest tests/test_defect_report.py -o addopts=""` run showing it passes unmodified.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: backlog item `42da1n`'s front matter pasted, showing `- Status: open`, `- Work-Kind: bug` and `- Blocks-Release: next`; the pasted `rg -n "emits_structured_tool_events" agent_workflows/host_sandbox_profile.py` output proving that field is STILL assigned in the identity branch, which is what shows this plan stayed inside its scope fence rather than fixing a second capability; and the pasted `python3 -m agent_workflows check release-gates` run showing no new violation.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the pasted BEFORE and AFTER summary lines of bare `python3 -m pytest`, each showing its own `N passed` count, plus a pasted run of `tests/test_defect_report.py` and `tests/test_host_capability_extension.py`. The suite gate for the whole plan lands here, so a plan cannot reach `executed` without both counts pasted. A claimed count with no pasted runner output is not acceptable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

APPROVAL STATEMENT. This plan replaces a capability assertion made from HOST IDENTITY with one made from an EXECUTED observation of each host's real resume argv, so `supports_session_resume` becomes True for both runner hosts and False for a host with no argv builder. It adds one probe, changes one assignment, deletes one line, adds two tests, corrects the prose it falsifies, and files the sibling defect it declines to fix.

WHAT AN APPROVER IS ACCEPTING, stated plainly because it is easy to misread. NO RUN CHANGES BEHAVIOR: the field gates nothing today (F-03), so what this fixes is a shipped operator-facing report and a trap for the next author, not a protection. The field is still gated to nothing afterwards, which is half of what the backlog item complains about (OQ-01 records why fixing the description first is nonetheless right). The sibling `emits_structured_tool_events` is still wrong afterwards and is filed rather than fixed (F-07, E-07), precisely because THAT one is consumed and flipping it would change a barrier decision.

SCOPE FENCE. Touch only the three paths in `Scope-Paths`, plus the backlog item E-07 mints through `aw backlog new`. Do NOT fix `emits_structured_tool_events`. Do NOT add a requirement to `ACTION_CAPABILITY_REQUIREMENTS`. Do NOT edit `runner_shared.py`, either runner module, `run_evidence.py`, `host_capability_registry.py`, or any spec. Do NOT modify `tests/test_defect_report.py`. Do NOT move the runner imports to module level (F-04: that is an import cycle). Do NOT rewrite what review `mjx7ne` or any executed plan RECORDS about this line.

HONESTY RULE. E-02's antigravity case MUST be observed failing before E-04 and its failure pasted into V-02; if it passes on first run the premise has changed and the plan must be re-scoped rather than marked complete. V-05's sabotage run MUST actually be performed: it is the only evidence that the new test detects a hardcoded table, which is this plan's own failure mode one level up. Paste actual runner output for every V-item; do not claim a suite result that was not run.

EXECUTION CONTRACT. Commit only the paths this plan names, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`. Verify the staged set before committing: this is a shared checkout and `host_sandbox_profile.py` is a file other work touches.

POST-GATE LIFECYCLE MOVE. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` above carries pasted evidence with `Result: verified`. If any V-item cannot be satisfied, leave the plan in `pending/` and report the blocker.
