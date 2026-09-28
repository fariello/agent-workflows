# IPD: Wire the host-capability preflight into the one shared dispatch point so its refusal can actually fire

- Date: 2026-09-28
- Kind: child
- Concern: `host_sandbox_profile.preflight_host_capabilities` is shipped, tested and correctly per-item, and NOTHING CALLS IT. Re-measured at HEAD `a11c0580` (the backlog item measured `7562ca6c`): `rg -c preflight_host_capabilities agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/runner_shared.py` exits 1 with no output, so the count is still zero in all three files. Spec `25kzda` 5.2's fail-closed rule ("If the descriptor cannot positively prove every capability required by an action, the engine starts no session and performs no mutation for that item"), its 5.4 rule-6/reason table row (`Required host capability unavailable` -> `failed` / `host_capability_unavailable`), and its 5.7 taxonomy row (`Host guarantee unavailable` -> "Refuse the item before session start; cascade dependents; continue independent items") all require a refusal that no run can produce. `run_selection_policy` already records this in code beside `SKIP_HOST_CAPABILITY_UNAVAILABLE` ("NOT REACHABLE TODAY ... so no current run emits this reason"), and `run_evidence.RUN_FINDING_CODES` nonetheless reports `RUN-HOST-CAPABILITY` as `BOUND` on the strength of the three predicates existing. This is the defect class `runner_shared.enforce_mixed_type_gate` names in its own docstring: a fully tested, importable, completely unreachable gate is indistinguishable from no gate at all.
- Scope: IN: call `preflight_host_capabilities` exactly once, from the ONE shared per-item dispatch point both hosts already route through (`runner_shared.execute_item_core`), immediately beside the existing `scope_target_stale` refusal that has the same item-local shape; record the refusal as `fail-gate` with `reason_code` `host_capability_unavailable`, the preflight's verbatim `RUN-HOST-CAPABILITY` message, a `host-capability-unavailable` event and a durable `host_capability_refusal` key, then return WITHOUT starting a session; let the existing `cascade_dependency_blocked` do the dependent cascade rather than writing a second one; and delete the two now-false "not reachable today" code comments. ALSO IN, and load-bearing rather than incidental (F-02): map the runner's `item["action"]` vocabulary (`execute`/`review`/`plan`) onto the contract's action vocabulary, which since plan `01reg8` contains only `read_only`. OUT, and this is the decision that keeps the plan honest (F-03, OQ-01): this plan does NOT add a capability requirement to any action, so after it lands the wired gate still refuses nothing on a real host. It closes the REACHABILITY defect the item names and leaves the separate question of what a mutating action must require to `b7tlsh`/`oq05nc`, which already own it. Also OUT: probing anything new, reinstating `ACTION_REVIEW`/`ACTION_MUTATE`/`ACTION_CONTRACTLESS_PROMPT`, touching `host_capability_registry.py` (a different concern), and amending spec `25kzda`'s 5.2 action table.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_selection_policy.py, tests/test_host_capability_wiring.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: 7bj5sa
- Set: 7bj5sa
- Order: 1
- Highest E allocated: 07
- Author: opencode
- Id: iot7hc

## Workflow history

- 2026-09-28 to-review (opencode): Graduated from backlog `7bj5sa`. Re-measured the zero-call-site claim at HEAD `a11c0580` and found it still true. Authoring also measured two things the backlog item does not state and which change the shape of the work: the only surviving action class requires nothing (plan `01reg8`), so wiring alone cannot make the gate refuse on any host; and `preflight_host_capabilities` RAISES `UnknownActionError` for the runner's own action names, so the naive wiring crashes every execute item. Both are recorded as F-02/F-03 with the design consequence in OQ-01.
- 2026-09-28 draft (opencode): created.

## Goal

Make the shipped host-capability preflight REACHABLE from a real run, so that spec `25kzda` 5.2/5.4/5.7's `host_capability_unavailable` refusal is a code path a run can execute rather than a tested function nothing calls, without inventing a capability requirement this repository cannot prove.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the baseline, and prove the gate is unreachable BEFORE changing anything

- [ ] E-01 RE-MEASURE the whole premise and write the result into the plan as an execution note, because three of this plan's load-bearing facts are dated and each has a cheap check. Record: (a) the call-site count, `rg -c "preflight_host_capabilities" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/runner_shared.py` (expected: no output, exit 1); (b) the action vocabulary, `python3 -c "from agent_workflows import host_sandbox_profile as h; print(h.ACTION_CLASSES, {a: r.required for a, r in h.ACTION_CAPABILITY_REQUIREMENTS.items()})"`; (c) that both hosts reach ONE dispatch function, `rg -n "execute_item_core" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py`. IF ANY HAS MOVED, SAY SO AND RE-SCOPE rather than proceeding: in particular, if some action has acquired a non-empty `required` tuple since authoring, then OQ-01's premise is gone and E-04's test expectations change from "proceeds" to "refuses". Trust the tree, not this plan's Concern.
  - Depends on: none
  - Expected outcome: a written, symbol-cited baseline stating zero call sites, `ACTION_CLASSES == ('read_only',)` with `read_only` requiring nothing, and `execute_item_core` called from both drivers; or an explicit statement of what moved and what it changes.
  - Execution state: pending

- [ ] E-02 WRITE THE FAILING TEST FIRST, in a new file `tests/test_host_capability_wiring.py`, so the reachability defect is pinned by something that fails before the wiring exists and passes after. The test must prove REACHABILITY, not the preflight's internal logic (which `tests/test_host_capability_extension.py` already covers with 38 passing cases). Two cases: (1) an AST or import-time assertion that `runner_shared` REFERENCES `preflight_host_capabilities` (this is the case that must FAIL first, and it is the direct inverse of the measurement in E-01a); (2) a call-through test that drives the refusal path with a descriptor forced to lack a required capability and asserts the item ends `fail-gate` with the spec's reason code and no session started. For (2), use the SHIPPED test seams rather than inventing one: `host_sandbox_profile.forced_runner_safety_verdicts` for the capability verdict (it is the documented save/restore seam and it restores on exception), and the synthetic-action pattern `tests/test_host_capability_extension.py::synthetic_gated_action` establishes for a requirement-bearing action, since no production action requires anything (F-03). DO NOT assert against a real host descriptor: `supports_fresh_verifier_session` probes True on Linux and False on darwin/win32 (measured, F-05), so a real-descriptor assertion is platform-dependent and would fail in CI on a different runner.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_host_capability_wiring.py -o addopts=""` FAILS on case (1) with a message naming the absent reference, and case (2) either fails or is skipped pending the wiring. The failure is pasted into V-02 as the before-state.
  - Execution state: pending

### Task group 2: the action-vocabulary bridge, then the call site

- [ ] E-03 ADD THE ACTION-NAME BRIDGE, in `runner_shared.py`, and make its fail-closed direction explicit. The runner's own action vocabulary is `execute` / `review` / `plan` (read from `item["action"]`; `execute_item_core` raises `DriverError` for anything else), while the contract's vocabulary is the single class `read_only`. `preflight_host_capabilities` RAISES `UnknownActionError` on an unrecognized action BY DESIGN ("that is a programming error in the caller, not a host that lacks a capability, and silently treating it as a refusal would hide the bug behind a plausible-looking outcome"), and it does so for every one of the runner's three names: measured, `preflight_host_capabilities("execute", caps, host="opencode", item="7bj5sa")` raises `UnknownActionError: unknown action class 'execute'; expected one of ['read_only']`. So a bare call at the dispatch point would crash EVERY execute item. Add a small explicit mapping (a module-level dict plus a function, not an inline `or`), and make the UNMAPPED case a refusal-free PASS with a recorded note rather than either a crash or a refusal. State the reason in the docstring: an action this contract has no row for is an action the contract makes no claim about, and converting "no policy" into "refused" would stop every run on a policy nobody wrote, while converting it into a crash would take down the dispatch path for the same reason. DO NOT re-add the three action constants `01reg8` deleted; that plan's E-04 comment explicitly forbids "restoring parity" without a consumer.
  - Depends on: E-02
  - Expected outcome: a named function in `runner_shared` maps `execute`/`review`/`plan` onto a contract action or onto an explicit no-policy sentinel, with a docstring stating the fail-closed reasoning, and no code path can reach `preflight_host_capabilities` with a name it would raise on.
  - Execution state: pending

- [ ] E-04 CALL THE PREFLIGHT AT THE ONE SHARED DISPATCH POINT. Place it in `runner_shared.execute_item_core`, immediately after the existing `scope_target_stale` refusal block and before `build_prompt`/`write_prompt`, and copy that block's shape deliberately rather than inventing a second one: it is the same item-local refusal class (refuse before session start, cascade dependents, continue independent items) and it already solves the two problems this call has. Specifically, follow its placement rationale (the shipped comment says "Placed before build_prompt/write_prompt to avoid orphan prompt files on refusal") and its `try/except` posture. On refusal, write the SAME five things that block writes, with this plan's vocabulary: an `attempts` entry with `"disposition": "fail-gate"`, `item["status"] = "fail-gate"`, a durable `item["host_capability_refusal"]` carrying the preflight's verbatim `message` and its `reason_code`, `save_state`, and an `events.jsonl` record with `"event": "host-capability-unavailable"` plus the missing capability names. Then `return` WITHOUT starting a session. Print the preflight's own `message` rather than composing a new one: it is spec `25kzda`'s verbatim text including the recovery command, and `format_host_capability_finding`'s docstring states a message without it is not spec-conforming. USE `fail-gate` AND NOT a new status token: `fail-gate` is in `TERMINAL_STATES_CANONICAL`, the `scope_target_stale` sibling already uses it, and `TERMINAL_STATUS_ALIASES` shows what inventing tokens costs (ten legacy spellings now aliased). PASS THE HOST LABEL the descriptor was built for, not the driver id: `detect_host_capabilities` is called with `"opencode"` in `oc_runipd._apply_execution_profile` and with the host name in `host_cmd._describe_host`, and the message interpolates `aw {host} run {selector}`, so a wrong value produces a recovery command an operator cannot run.
  - Depends on: E-03
  - Expected outcome: `rg -c "preflight_host_capabilities" agent_workflows/runner_shared.py` returns at least 1; E-02's case (1) now passes; a forced-unavailable descriptor drives an item to `fail-gate` with reason `host_capability_unavailable`, no prompt file written and no session started.
  - Execution state: pending

- [ ] E-05 DO NOT WRITE A SECOND CASCADE. Confirm by reading `cascade_dependency_blocked` that a `fail-gate` item ALREADY cascades to its dependents, and record the evidence in an execution note instead of adding cascade code. The mechanism: that function marks a queued item `fail-depend` when a prerequisite's status `st in TERMINAL_STATES and st not in required`, and `fail-gate` is in `TERMINAL_STATES` while `EXECUTION_SUCCESS_STATES == {"executed"}`, so a capability-refused prerequisite is already a dead edge. It runs at the top of each drain iteration, which the code comments confirm. This satisfies spec `25kzda` 5.4 rule 7 and the preflight's own `cascade_dependents=True` WITHOUT a parallel propagation path; writing one would be the "two functions gave opposite answers to one question" defect that function's docstring records as a measured production failure (run `run-20260904T042705Z-1025943`, which killed four items of a well-formed Set).
  - Depends on: E-04
  - Expected outcome: a written statement, citing `cascade_dependency_blocked` by symbol and the two state-set memberships by value, that the cascade is already correct; and a test in E-02's file asserting a dependent of a capability-refused item reaches `fail-depend`. ZERO lines of new cascade logic.
  - Execution state: pending

### Task group 3: retract the two now-false comments, and run the suite

- [ ] E-06 DELETE THE TWO "NOT REACHABLE" CLAIMS, which this plan falsifies, and replace each with what is then true. Both are in `run_selection_policy.py`: the comment block above `SKIP_REASON_SOURCES` that says `host_capability_unavailable` is per-artifact and spec-named "But measured: neither driver nor `runner_shared` calls that preflight (zero occurrences of `preflight_host_capabilities` in all three files), so no run can produce it TODAY ... this note exists so nobody reports it as a reason a current run can emit"; and the `SKIP_HOST_CAPABILITY_UNAVAILABLE` entry in that mapping, whose text ends "NOT REACHABLE TODAY: neither driver calls that preflight (measured zero call sites), so no current run emits this reason". Replace both with the post-wiring truth AND its honest limit, in one place each: the reason is now reachable through `runner_shared.execute_item_core`, and on a real host today no production action requires a capability, so the path is reachable but not yet exercised by any shipped requirement (OQ-01). DO NOT overstate this as "the gate now protects runs"; that is the same fail-open claim the original comment was written to prevent, pointed the other way. Leave `run_evidence.py`'s `RUN-HOST-CAPABILITY` row alone: its `BOUND` binding and its three named predicates are unchanged by this plan, and its `NonMaskableClass` entry already names the preflight as the upstream decider.
  - Depends on: E-05
  - Expected outcome: `rg -n "NOT REACHABLE TODAY|no current run can emit|no run can produce it TODAY" agent_workflows/` returns nothing, and neither replacement claims a protection that OQ-01 records as absent.
  - Execution state: pending

- [ ] E-07 Run the bare suite, `python3 -m pytest`, and compare against a baseline taken the same way BEFORE any edit in this plan. Bare is required: `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, and adding `-n0` makes this suite several times slower here while a second `-q` suppresses the `N passed` summary line this plan must paste.
  - Depends on: E-06
  - Expected outcome: no new failures relative to the same-day baseline, with both counts pasted. `tests/test_host_capability_extension.py` (38 passing at authoring) and `tests/test_host_sandbox_profile.py` must pass UNCHANGED: neither is in `Scope-Paths`, and this plan changes no preflight behavior, so a failure there means the wiring altered a contract it was supposed to consume.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Presence-based inference is FORBIDDEN in this module family, in writing, with a measured justification (`host_sandbox_profile` module docstring, "WHY THE PROBE EXECUTES INSTEAD OF INSPECTING": every signal on the development host said "sandbox available" while `unshare -Umr true` failed with `Operation not permitted`). This plan adds no probe and infers no capability; it only calls an existing checker.
- A per-item refusal has an established shape in this repository, and it is not invented per plan: the `scope_target_stale` block in `execute_item_core` (attempt entry + `fail-gate` + durable reason key + `save_state` + event + early `return`, placed before prompt authoring) is the template E-04 follows.
- Terminal status tokens are a CLOSED canonical vocabulary of twelve (`TERMINAL_STATES_CANONICAL`), and `TERMINAL_STATUS_ALIASES` is the standing record of what inventing new ones costs. Hence `fail-gate` rather than a new token.
- Skip-reason codes are a CLOSED set and `skip_reason_text` raises on an unknown code, deliberately, so that "a reason is a value rather than an ad-hoc string". `host_capability_unavailable` is ALREADY in that set with a label and a remedy ("inspect the refused capability with `aw host capabilities`, then run the item on a host that satisfies it"), so this plan adds no vocabulary.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | The zero-call-site claim is still true at a newer HEAD than the backlog item measured. | `rg -c "preflight_host_capabilities"` over `oc_runipd.py`, `agy_runipd.py`, `runner_shared.py` exits 1 with no output at HEAD `a11c0580`; the item measured `7562ca6c`. | The premise holds; no re-scope needed. |
| F-02 | A NAIVE wiring crashes every execute item, so the bridge in E-03 is required, not cosmetic. | `preflight_host_capabilities("execute", caps, host="opencode", item="7bj5sa")` raises `UnknownActionError: unknown action class 'execute'; expected one of ['read_only']`. The raise is deliberate (its docstring: "that is a programming error in the caller"). | E-03 exists and precedes E-04. A reviewer should treat any plan that wires this without an action bridge as broken. |
| F-03 | WIRING ALONE CANNOT MAKE THE GATE REFUSE ANYTHING ON A REAL HOST. | `ACTION_CLASSES == ('read_only',)` and `ACTION_CAPABILITY_REQUIREMENTS['read_only'].required == ()`, both measured; plan `01reg8` E-04 deleted the other three classes on maintainer ruling `4h7tt0` OQ-02 because nothing consumed their verdicts. So `preflight_host_capabilities('read_only', ...)` returns `ok=True` on every host. | The plan's deliverable is REACHABILITY, stated as such in Scope and OQ-01, not protection. Tests must use the synthetic-action seam, since no production action can produce a refusal. |
| F-04 | There is exactly ONE shared per-item dispatch point, so one call site covers both hosts. | `runner_shared.execute_item_core` is called from `oc_runipd.execute_item` and `agy_runipd`'s equivalent; `agy_runipd` records that the two were "unified into `runner_shared.execute_item_core`". | E-04 edits one function, not two drivers. A per-driver copy would be the drift both hosts' comments warn about. |
| F-05 | The one genuinely probed runner-safety capability is PLATFORM-DEPENDENT, so a real-descriptor test assertion is not portable. | Measured: `supports_fresh_verifier_session` is True for `linux`, False for `darwin` and `win32`; `supports_commit_gateway` is False everywhere and is declared-never-probed by design. | E-02 forbids real-descriptor assertions and requires the forced-verdict seam. |
| F-06 | The cascade this plan needs already exists and is already correct for `fail-gate`. | `cascade_dependency_blocked` blocks a dependent when a prerequisite is `st in TERMINAL_STATES and st not in required`; `fail-gate` is in `TERMINAL_STATES`, `EXECUTION_SUCCESS_STATES == {"executed"}`. | E-05 writes ZERO cascade code and instead records the evidence. |
| F-07 | Two shipped comments become FALSE the moment E-04 lands, and one of them is a warning to future readers. | `run_selection_policy.py`: the `SKIP_REASON_SOURCES` preamble ("no run can produce it TODAY ... this note exists so nobody reports it as a reason a current run can emit") and the `SKIP_HOST_CAPABILITY_UNAVAILABLE` source string ("NOT REACHABLE TODAY"). | E-06 retracts both in the same change, so the tree never asserts an unreachability this plan removed. |
| F-08 | `run_evidence` already reports `RUN-HOST-CAPABILITY` as `BOUND` on predicate existence alone, which is why this defect was invisible in the findings table. | `RUN_FINDING_CODES`' row names `preflight_host_capabilities`, `format_host_capability_finding` and `check_action_capabilities` with `binding=BOUND`; the 2026-09-05 re-measurement comment says it became BOUND because `mjx7ne` "executed and shipped" the function. | Out of scope to change the binding model, but worth a reviewer's attention: `BOUND` means "a predicate exists", not "a run can reach it". Noted in Deferred. |
| F-09 | The deferral was DELIBERATE and documented, so this plan completes a known obligation rather than fixing an oversight. | `mjx7ne`'s Deferred section: "WIRING THE PREFLIGHT INTO BOTH RUNNER MODULES ... Deferred here so this plan does not touch `oc_runipd.py`/`agy_runipd.py` at all"; its Scope check concedes "after this plan the capability check EXISTS and is tested but is not yet consulted by a live run, so it prevents nothing until the follow-up wires it". The module docstring repeats it as an "HONEST LIMIT". | This plan IS that follow-up. E-06 must also leave the module docstring's honest limit accurate; if it states no runner consults the preflight, it is in `host_sandbox_profile.py`, which is NOT in `Scope-Paths` (see Scope check). |

## Proposed changes (ordered, validatable)

1. Baseline the three dated facts and pin the defect with a test that fails first (E-01, E-02).
2. Add the action-vocabulary bridge, with an explicit no-policy pass for an unmapped action (E-03).
3. Call the preflight once, at `execute_item_core`'s existing refusal site, recording `fail-gate` + `host_capability_unavailable` + the verbatim message and returning before any session (E-04).
4. Verify, rather than rebuild, the dependent cascade (E-05).
5. Retract the two now-false unreachability comments, without overclaiming protection (E-06).
6. Bare suite, before-and-after (E-07).

## Deferred / out of scope (with reason)

- ADDING A CAPABILITY REQUIREMENT TO A PRODUCTION ACTION. This is the change that would make the gate refuse something real, and it is deliberately not here. It reverses a maintainer ruling (`4h7tt0` OQ-02, 2026-09-10, executed by `01reg8`) that removed unenforced verdicts precisely because nothing consumed them, and it needs a spec-level answer about what a mutating action must prove. See OQ-01.
  - Carrier: b7tlsh
- REINSTATING `ACTION_REVIEW` / `ACTION_MUTATE` / `ACTION_CONTRACTLESS_PROMPT`. `01reg8` E-04 deleted them and left an explicit instruction not to "restore parity" by re-adding the constants without a consumer. Wiring needs a bridge, not the old constants back.
  - Carrier-Declined: There is nothing to carry. This row records a PROHIBITION on this plan rather than an outstanding defect: the maintainer's ruling that deleted those constants is the correct state, so no future work is owed and a carrier would name an obligation that does not exist. E-03's bridge is what makes the deletion survivable, and V-03 enforces it inside this plan.
- BUILDING A REAL PUSH-DENIAL BOUNDARY, the one mechanism that would give a mutating action something non-evadable to require. Out of scope by size: the source analysis calls it a security-boundary design of `1o4eif` magnitude needing a spec-level decision before any code.
  - Carrier: oq05nc
- AMENDING SPEC `25kzda`. Nothing in this plan changes a contract the spec states. 5.2's four-row action table is deliberately un-narrowed (`01reg8` OQ-03 accepted the divergence and recorded it in code), and 5.4/5.7's rows describe exactly the behavior this plan makes reachable. `Scope-Paths` therefore names no `.spec.md` file, which is the declaration the runners' spec-edit announcer reads.
  - Carrier-Declined: Nothing is owed. This row is a scope boundary rather than a dropped obligation: the spec already requires the behavior this plan implements, so there is no divergence for a successor to reconcile. The one spec question that IS live (whether 5.2 should claim commit-gateway enforcement at all) is carried by `b7tlsh` on the first row above and is not duplicated here.
- CHANGING THE `BOUND` BINDING MODEL IN `run_evidence` (F-08). That `RUN-HOST-CAPABILITY` reads `BOUND` while unreachable is a real weakness in what `BOUND` asserts, and it is a change to a 13-code table with its own count-enforcing tests (`01reg8`'s predecessor measured four hardcoded-13 assertions plus a runtime `RC-COUNT` validation that made the shipped table report itself invalid when a row was removed without owning the count). Filed during authoring rather than left to the executor.
  - Carrier: u7bfks
- `host_capability_registry.py`. A different concern (skill-delivery evidence with expiry), kept out by `mjx7ne` F3 for the same reason.
  - Carrier-Declined: Nothing is owed. The module is a different concern that this plan neither needs nor degrades, so excluding it leaves no gap: no obligation arises from not editing an unrelated module. The exclusion is recorded because a reader might expect a capability change to touch every file with "capability" in its name.

## Scope check

- Over-scope: none. `runner_shared.py` carries E-03/E-04/E-05, `run_selection_policy.py` carries E-06, and the test file is new.
- Under-scope, DELIBERATE and stated plainly: after this plan the gate is REACHABLE but still refuses nothing on any real host, because the only action class requires nothing (F-03). An operator reading "the host-capability gate is wired" must not conclude a protection was added. That is the honest consequence of keeping the maintainer's ruling intact, and it is recorded in OQ-01, in E-06's replacement comment, and here.
- `host_sandbox_profile.py` is deliberately NOT in `Scope-Paths`, so its module docstring's "HONEST LIMIT: nothing in the runners consults this preflight yet" will be stale after E-04. The executor must NOT edit it silently: either request a scope amendment at review (one sentence, in the module whose contract it describes) or leave it and record the staleness. Raised as OQ-02 so a reviewer decides rather than an executor improvising.
- `runner_shared.py` is the most contended file in this repository. Re-read `execute_item_core` immediately before editing and verify the staged set before committing.

## Required tests / validation

- New `tests/test_host_capability_wiring.py` must pass, with the reachability case having been observed to FAIL before E-04 (the before-state is pasted into V-02).
- `tests/test_host_capability_extension.py` (38 passing at authoring) and `tests/test_host_sandbox_profile.py` must pass UNCHANGED. Neither is in `Scope-Paths`; a failure there means this plan altered the contract it was meant to consume.
- The bare suite `python3 -m pytest`, before and after, with both summary lines pasted.

## Spec / documentation sync

- No spec amendment. This plan implements behavior spec `25kzda` 5.2/5.4/5.7 ALREADY requires and does not change any contract the spec states; `Scope-Paths` names no `.spec.md` file, which is the declaration the runners announce at run start.
- The two code comments in `run_selection_policy.py` that assert unreachability ARE the documentation of this defect, and E-06 retracts them in the same change, so the tree never carries a claim this plan falsified.
- `host_sandbox_profile.py`'s module docstring carries the same claim and is out of scope; see the Scope check and OQ-02.

## Open questions

### OQ-01: After this plan the gate is reachable but still refuses nothing. Is reachability alone the right deliverable, or must this plan also give some action a real requirement?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: b7tlsh
- Resolution or deferral rationale: DEFAULT, and what this plan is written to: REACHABILITY ALONE. The backlog item's defect is that "the gate exists and is unreachable, which from the operator's seat is indistinguishable from no gate", and wiring the call site fixes exactly that, verifiably, with a test that fails first. Adding a requirement is a DIFFERENT change with a different risk profile: it would make items refuse on hosts that run fine today, and it would reverse a maintainer ruling (`4h7tt0` OQ-02, executed by `01reg8`) made on the measured ground that nothing consumed those verdicts. Non-blocking because the plan is correct and complete under the default, and because the alternative has live carriers: `b7tlsh` owns the commit-gateway claim and `oq05nc` owns a real push-denial boundary. THE HONEST COST OF THE DEFAULT, stated so the maintainer can overrule it cheaply: a reader of the changed code could conclude the runner now enforces host guarantees, when what it enforces is a policy that is currently empty. E-06's comment and the Scope check both say so explicitly; if the maintainer wants the stronger change, it is a follow-up plan, not an edit to this one.

### OQ-02: `host_sandbox_profile.py`'s docstring will be stale after E-04, and the file is out of scope. Amend it here, or leave it and record the staleness?

- Blocking: no
- Status: open
- Owner: reviewer
- Carrier-Declined: This question is answered, either way, INSIDE this plan and leaves no work behind it. Under the default (amend) the correction lands in this plan's own diff after a one-line scope amendment; under the alternative (decline) the executor records the staleness and a backlog item is filed AT THAT MOMENT, which is a step this plan already instructs rather than an obligation a successor must discover. There is therefore no outstanding obligation for a carrier to own at authoring time. The adjacent obligation that DOES outlive this plan, whether the spec should claim commit-gateway enforcement at all, is carried by `b7tlsh` in the Deferred section and is not duplicated here.
- Resolution or deferral rationale: DEFAULT: AMEND IT, via a one-sentence scope amendment at review that adds `agent_workflows/host_sandbox_profile.py` to `Scope-Paths` for that edit and nothing else. The docstring's "HONEST LIMIT: nothing in the runners consults this preflight yet. ... so today this prevents nothing on its own" is the module's own contract statement, and leaving it false in the same commit that falsifies it is exactly the drift E-06 exists to prevent one file over. Raised rather than assumed because a mid-execution scope expansion is what the finalize scope gate refuses, so the decision belongs at review where it is cheap. If the reviewer declines, the executor must leave the file untouched and record the staleness in the execution note, and a backlog item should carry the correction.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted output of all three baseline commands, with the HEAD they were run at. The `rg -c` invocation must be shown with its exit status, since "no output" is the expected result and an empty paste is otherwise indistinguishable from a command that was never run. If any fact moved, the paste must be accompanied by the re-scope statement.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted FAILING run of `python3 -m pytest tests/test_host_capability_wiring.py -o addopts=""` taken BEFORE E-04, including the assertion message naming the absent reference. A test that passed on its first run is not evidence of a pinned defect and must be rejected here.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the bridge function quoted from the file, plus a pasted scratch run showing that each of `execute`, `review` and `plan` reaches a verdict WITHOUT raising `UnknownActionError`, and that an unmapped name takes the documented no-policy path rather than raising or refusing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `rg -c "preflight_host_capabilities" agent_workflows/runner_shared.py` returning at least 1; the now-PASSING run of the reachability case; and the pasted refusal-path test output showing the item's terminal status is `fail-gate`, its recorded reason is `host_capability_unavailable`, the message is the preflight's verbatim `RUN-HOST-CAPABILITY` text including the `aw <host> run <selector>` recovery command, and NO prompt file was written for the refused item.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the pasted test output showing a dependent of a capability-refused item reaches `fail-depend`, AND a `git diff` (or equivalent) demonstrating ZERO new cascade logic was added. The second half is the point of the item: a passing cascade test alongside a hand-written cascade would be the duplicated-predicate defect this item exists to avoid.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `rg -n "NOT REACHABLE TODAY|no current run can emit|no run can produce it TODAY" agent_workflows/` returning nothing, plus both replacement comments quoted in full so a reviewer can confirm neither claims a protection OQ-01 records as absent.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the pasted BEFORE and AFTER summary lines of bare `python3 -m pytest`, plus a pasted run of `tests/test_host_capability_extension.py` and `tests/test_host_sandbox_profile.py` showing both pass with those files unmodified (`git status --short` over the two paths showing no change).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

APPROVAL STATEMENT. This plan makes a shipped, tested, unreachable gate reachable from the single dispatch point both hosts already share. It adds one call, one small action-name bridge, and one new test file, and it retracts two comments it falsifies. It does NOT add a capability requirement, does not reverse the maintainer's `4h7tt0` OQ-02 ruling, does not probe anything, and does not amend a spec.

WHAT AN APPROVER IS ACCEPTING, stated plainly because it is easy to misread: after execution the `host_capability_unavailable` refusal is a path a run CAN take, and on a real host it still will not, because the only surviving action class requires nothing (F-03, OQ-01). If that is not the outcome you want, overrule OQ-01 and the work becomes a larger, spec-touching plan.

SCOPE FENCE. Touch only the three paths in `Scope-Paths`. Do not edit `host_sandbox_profile.py` (see OQ-02), `run_evidence.py`, either driver module, or any spec. Do not add a terminal status token. Do not write a second cascade. `runner_shared.py` is heavily contended: re-read `execute_item_core` immediately before editing, and verify the staged set before committing.

HONESTY RULE. E-02's test MUST be observed failing before E-04 and its failure pasted into V-02. If it passes on first run, the premise has changed and the plan must be re-scoped rather than marked complete. Paste actual runner output for every V-item; do not claim a suite result that was not run.

EXECUTION CONTRACT. Commit only the paths this plan names, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`.

POST-GATE LIFECYCLE MOVE. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` above carries pasted evidence with `Result: verified`. If any V-item cannot be satisfied, leave the plan in `pending/` and report the blocker.
