# IPD: extend the shipped sandbox capability contract with the runner-safety guarantees and a fail-closed action preflight

- Date: 2026-08-30
- Kind: child
- Concern: The runners assume both hosts can do the same things. When that is false the runner asks a host for something it cannot do and the operator gets a confusing downstream failure instead of a clear refusal. The shipped `host_sandbox_profile.HostSandboxCapabilities` already carries a typed, PROBED capability contract for the sandbox/process concerns, but it says nothing about the runner-safety guarantees a lifecycle action actually depends on (commit gateway, deny-push, fresh verifier session), and nothing compares what an ACTION needs against what the host proved it can do.
- Scope: EXTEND the shipped contract in `host_sandbox_profile.py` with the missing runner-safety capabilities and their probes, add an action-to-capability requirement map plus a fail-closed `RUN-HOST-CAPABILITY` preflight, and expose read-only inspection verbs. Excludes creating a second capability module, excludes any change to the skill-delivery registry (`host_capability_registry.py`, a different concern), excludes the sandbox mechanism itself (owned by `1o4eif`), and excludes wiring the preflight into both runner modules (deferred, see OQ-01).
- Scope-Paths: agent_workflows/host_sandbox_profile.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_host_capability_extension.py
- Item-Dependencies: none
- Status: to-review
- Set: hostcap
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: mjx7ne
- Blocks-Release: next
- From-Backlog: none

## Workflow history

- 2026-08-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): SUPERSEDES `a54m79` (detrun-02) at the maintainer's direction. `a54m79` had already been marked "REPLAN - DO NOT EXECUTE" by its own second review, and it blocked four downstream plans by refusing at pre-execution on two unresolved maintainer questions. Both are answered here from repository evidence and recorded in OQ-01/OQ-02. The substance of `a54m79` is PRESERVED, not discarded: its capability vocabulary, its action-requirement idea, and its fail-closed preflight are all real gaps. What changes is the OWNER, from a net-new `host_capabilities.py` to the module that already shipped the same kind of contract.

## Goal

Make the runner refuse clearly, up front, when a host cannot provide a guarantee the action requires, by extending the capability contract that already exists rather than building a second one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: extend the shipped contract

- [ ] E-01 Add the missing runner-safety capability fields to the shipped `HostSandboxCapabilities` dataclass in `host_sandbox_profile.py`. MEASURED starting point, so the executor does not rediscover it: the dataclass today carries `supports_inline_permissions`, `supports_read_only_phase`, `supports_session_resume`, `emits_structured_tool_events`, `emits_child_permission_events`, `supports_process_tree_kill`, `supports_os_sandbox`, `platform`, `sandbox_mechanism`, `probe_notes`. Add `supports_commit_gateway`, `supports_deny_push`, and `supports_fresh_verifier_session`. Every new field defaults to the CONSERVATIVE value (not-supported), so an unprobed host is treated as lacking the guarantee rather than as having it. Do NOT rename or reorder existing fields: `1o4eif`'s dispatch reads them and its 27 tests pin them.
  - Depends on: none
  - Expected outcome: the extended dataclass carries the three new fields with conservative defaults; `1o4eif`'s existing sandbox tests pass UNCHANGED; a host descriptor built with no probes reports the new capabilities as unsupported.
  - Execution state: pending

- [ ] E-02 Implement probes for the three new capabilities, following the shape the module already uses (`_probe_bwrap`, `_probe_landlock`, `_probe_userns` and the shared `_run_probe` helper; locate them by symbol). Each probe must ATTEMPT the thing and report what happened rather than inferring from a config file or a version string, which is the discipline the shipped probes already follow. A probe that cannot run reports not-supported, never supported-by-assumption. Record the outcome in the existing `probe_notes` channel rather than adding a second reporting path.
  - Depends on: E-01
  - Expected outcome: each new capability has a probe that returns a definite supported/not-supported verdict with a note; a probe that raises or times out yields not-supported; no probe reports supported without having observed the behavior.
  - Execution state: pending

- [ ] E-03 Add the mock-probe injection seam so degraded, unsupported, and stale-cache host scenarios are testable without owning those hosts. Reuse the module's existing injection style if it has one (check `_run_probe` for an injectable runner before adding a parameter); the shipped module was written to be testable, so prefer its seam over a new one.
  - Depends on: E-02
  - Expected outcome: a test can force any capability to any verdict without spawning a real host; the production path is unchanged when no mock is supplied.
  - Execution state: pending

### Task group 2: gate the action, not the host

- [ ] E-04 Define the action-to-capability requirement map and the checker. An `execute` action needs stronger guarantees than a `review` action, which is the whole point: a review that cannot commit is fine, an execution that cannot route commits through a gateway is not. Implement `check_action_capabilities(...)` returning a definite verdict plus the specific missing capabilities, so the caller can name them. Keep the map DATA, not branching logic, so a reader can see the policy in one place.
  - Depends on: E-01
  - Expected outcome: the map states, per action, which capabilities are required; the checker names every missing capability rather than failing on the first; a fully-capable host passes for every action.
  - Execution state: pending

- [ ] E-05 Add the `RUN-HOST-CAPABILITY` finding code and make the check FAIL CLOSED: a missing required capability refuses the action with a message naming the host, the action, and the missing capabilities. This finding code is CONSUMED BY A SIBLING: plan `7f7782` (detrun-05) references `RUN-HOST-CAPABILITY` seven times as one of its 13 deterministic checks, and it is the only downstream plan that depends on this work at all (verified: `kaygwo` and `k7o7el` reference none of this plan's symbols). So the code string and its meaning are a contract with `7f7782`; do not rename it.
  - Depends on: E-04
  - Expected outcome: an action requiring an unsupported capability is REFUSED with a message naming host, action, and missing capabilities; a satisfied action proceeds; the finding code is exactly `RUN-HOST-CAPABILITY`.
  - Execution state: pending

- [ ] E-06 Add read-only inspection verbs (`aw host probe <host>` and `aw host capabilities [host]`) and `tests/test_host_capability_extension.py`. Tests must cover: the three new fields defaulting conservative; each probe's supported and not-supported paths; the mock seam; the requirement map per action; the fail-closed refusal naming the missing capabilities; and `1o4eif`'s existing sandbox tests still passing. CHECK BEFORE ADDING THE VERBS whether `command_surface.py` requires a declaration for a new command family; the repo has CLI-conformance tests that fail on undeclared parser leaves, and this plan declares that file for exactly that reason.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: both verbs work and are read-only (no probe side effects on the repo); the test module passes; the CLI-conformance tests pass; `1o4eif`'s tests pass unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE CONTRACT ALREADY EXISTS and is the thing to extend. `host_sandbox_profile.HostSandboxCapabilities` is a typed, probe-backed capability descriptor with fail-closed dispatch (`select_execution_profile` raises `HardModeUnavailableError` rather than silently degrading). It shipped with `1o4eif` and carries 27 passing tests.
- THE SKILL REGISTRY IS A DIFFERENT CONCERN, and `a54m79`'s own second review established this after its first review got it wrong. `host_capability_registry.py` is keyed on skill-import tiers (`t1_policy`/`t2_layout`/`t3_global`) with negative-probe classes like `missing_skill` and `stale_adapter`. It is about DELIVERING skills to hosts, not about what a host can guarantee at runtime. Do not fold this work into it and do not treat its existence as making this work redundant.
- The shipped probes ATTEMPT rather than inspect. `_probe_bwrap`, `_probe_landlock`, `_probe_userns` all try the mechanism and report; none infers capability from a version number. E-02 must follow that.
- `probe_notes` already exists as the reporting channel for why a probe concluded what it did. Reuse it.
- Only ONE downstream plan needs this work. Measured across the three: `7f7782` references `RUN-HOST-CAPABILITY` 7 times; `kaygwo` and `k7o7el` reference nothing from this plan. That is why this plan is scoped narrowly and why unblocking it unblocks the chain.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `a54m79` Goal section | The superseded plan had ALREADY been marked unexecutable by its own reviewer: its Goal opens `REPLAN - DO NOT EXECUTE`. It nonetheless sat `approved` and was launched, refusing at pre-execution and cascading four dependents to `dependency-blocked`. A plan that knows it must be replanned should not have been approved; that is a process gap worth noting separately from this plan's content. | the plan file's own Goal text; run-20260830T202022Z-3475919 showing `a54m79` blocked in 1s and 4 items cascading |
| F2 | HIGH | `host_sandbox_profile.py` | The overlap that motivated superseding: the shipped module already provides the typed capability descriptor, the probe pattern, and fail-closed dispatch. `a54m79` would have created `host_capabilities.py` with `HostCapability`/`CapabilityAssurance`/`HostCapabilityDescriptor`, a parallel vocabulary for the same guarantees. | `HostSandboxCapabilities` field list and `select_execution_profile` / `detect_host_capabilities` / `HardModeUnavailableError` read at HEAD |
| F3 | MED | `a54m79` vs `host_capability_registry.py` | The overlap is PARTIAL, not total, and this correction matters because it is why the work survives at all. The skill-delivery registry does NOT cover commit-gateway, deny-push, or fresh-verifier-session. Those are genuine gaps `a54m79` identified correctly. Discarding the plan wholesale would have lost real findings. | `a54m79`'s pass-2 review text correcting its own pass-1 "already shipped" claim; the registry's tier/probe vocabulary |
| F4 | MED | `7f7782` | `RUN-HOST-CAPABILITY` is a CROSS-PLAN CONTRACT, not an internal name. `7f7782` cites it 7 times as one of 13 deterministic checks and states the code greps to zero today. Renaming it would silently break that plan. | `grep -c RUN-HOST-CAPABILITY` in `7f7782` = 7; zero occurrences in the package |
| F5 | LOW | `kaygwo`, `k7o7el` | Neither references any symbol from this work, so their `dependency-blocked` status was purely transitive through `a54m79`. Landing this plan unblocks the chain without either needing anything from it. | grep for this plan's symbols in both files returned nothing |

## Proposed changes (ordered, validatable)

1. Extend the shipped dataclass with three conservative-default capability fields (E-01).
2. Probe them by attempting, in the module's existing probe style (E-02).
3. Reuse or add the mock seam so degraded hosts are testable (E-03).
4. Declare the action-to-capability policy as data plus a checker (E-04).
5. Refuse fail-closed under the `RUN-HOST-CAPABILITY` code `7f7782` expects (E-05).
6. Add read-only inspection verbs and the tests (E-06).

## Deferred / out of scope (with reason)

- WIRING THE PREFLIGHT INTO BOTH RUNNER MODULES. This was `a54m79`'s E-05 and is the single reason its OQ-03 wanted to wait for `rununify`. Deferred here so this plan does not touch `oc_runipd.py`/`agy_runipd.py` at all, which removes the sequencing conflict entirely rather than answering it (see OQ-01). The checker is usable by anything that imports it; a follow-up wires the call sites once the runner situation settles.
- CREATING A SECOND CAPABILITY MODULE. Explicitly rejected; that was the defect in the superseded plan.
- CHANGING THE SKILL-DELIVERY REGISTRY. A different concern (F3).
- THE SANDBOX MECHANISM ITSELF. Owned by `1o4eif`, already shipped.

## Scope check

- Over-scope: none. `host_sandbox_profile.py` carries E-01 through E-05, `cli.py` and `command_surface.py` carry the verbs, and the test module is new.
- Under-scope, DELIBERATE: the runner wiring is out (see Deferred). The honest consequence, stated rather than hidden: after this plan the capability check EXISTS and is tested but is not yet consulted by a live run, so it prevents nothing until the follow-up wires it. That is the price of removing the `rununify` entanglement, and it is the right trade because the vocabulary is what `7f7782` needs.
- `cli.py` is heavily contended in this repo. Re-read it immediately before editing and verify the staged set before committing.

## Required tests / validation

- `tests/test_host_capability_extension.py` must pass with every case in E-06.
- `1o4eif`'s `tests/test_host_sandbox_profile.py` must pass UNCHANGED (27 tests at time of writing). It is NOT in `Scope-Paths`; if a change to the shared dataclass breaks it, the extension is wrong, not the test.
- The CLI-conformance tests must pass, since this adds a command family. If they were already failing at your baseline for unrelated undeclared leaves, attribute those by NAME and prove this family is not among them.
- FALSIFIABILITY: the fail-closed refusal must be shown REFUSING against a host descriptor with a required capability set to unsupported, and PROCEEDING when it is supported. A test that only checks the happy path does not demonstrate a gate.
- INVOKE THE SUITE BARE: `python3 -m pytest` and `python3 -m pytest -m ""`. Do NOT add `-n auto` or a second `-q`.
- BASELINE IS A MEASUREMENT: take your own before/after counts with the `git rev-parse HEAD` they were measured at. This repo's baseline is moving hourly.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- Spec `25kzda` Section 4.2 enumerates the 13 deterministic `RUN-*` checks including `RUN-HOST-CAPABILITY`. This plan implements that one code; no spec text change is required, but the executor should record which of the 13 now exists so `7f7782` can see it.
- If `host_sandbox_profile.py` carries a module docstring describing its capability set, extend it to cover the three new fields rather than leaving it describing only the sandbox concerns.

## Open questions

### OQ-01: Must the runner wiring wait for `rununify`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE QUESTION IS DISSOLVED, not answered, and that is why this plan can run now. The superseded `a54m79` asked it because its E-05 edited BOTH runner modules, which would double the surface `rununify` must reconcile; its own recommendation was to wait, which would have parked five plans behind a Set whose child plans are not written and whose sequencing is only partly authorized. This plan instead DEFERS the runner wiring entirely (see Deferred), so it touches neither runner and the conflict cannot arise. The capability vocabulary and the checker, which are what `7f7782` actually needs, land immediately. The honest cost is in the Scope check: the gate is not yet consulted by a live run.

### OQ-02: Which module owns the typed host-capability contract?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `host_sandbox_profile.py`, the module that already shipped with `1o4eif`. Resolved from repository evidence at the maintainer's direction. It already provides exactly this KIND of thing: a typed dataclass of capabilities, probes that attempt rather than infer, a `probe_notes` reporting channel, and fail-closed dispatch that raises rather than degrading silently. Building `a54m79`'s parallel `host_capabilities.py` would have produced two vocabularies for one concept, which is the duplication this repo repeatedly pays for (compare `dhuape`, `rununify`). Note the boundary carefully, because the superseded plan's first review got it wrong: the SKILL-DELIVERY registry `host_capability_registry.py` is a different concern and is NOT the owner either (F3).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the extended dataclass showing the three new fields and their conservative defaults. Paste a descriptor built with NO probes showing all three reporting unsupported. Paste `tests/test_host_sandbox_profile.py` passing UNCHANGED with its count.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each of the three probes, paste a supported and a not-supported outcome with the `probe_notes` text. Paste a probe that raises or times out yielding not-supported. Show that no probe returns supported without an observation, by pasting the code path rather than asserting it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a test forcing a capability to each verdict via the mock seam. State whether you reused the module's existing injection seam or added one, and if added, why the existing one did not fit. Paste evidence the production path is unchanged with no mock supplied.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the requirement map showing it is DATA. Paste the checker naming MULTIPLE missing capabilities in one verdict, not just the first. Paste a fully-capable host passing every action.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the refusal for a host missing a required capability, showing the message names host, action, and the specific missing capabilities. Paste the same action PROCEEDING when the capability is supported; a one-sided demonstration does not show a gate. Paste a grep proving the finding code string is exactly `RUN-HOST-CAPABILITY`, matching what `7f7782` expects.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste both verbs' output and evidence they are read-only (no repo mutation, `git status` clean after). Paste the new test module passing. Paste the CLI-conformance tests passing, or the attributed pre-existing failures. State whether `command_surface.py` needed a declaration and what you found.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 6 E-leaves across 2 task groups, under the thresholds. One concern throughout: extend the existing capability contract so an action can be refused when its host cannot support it.

Open questions: BOTH RESOLVED, and neither needs a maintainer decision now. OQ-02 assigns ownership to the shipped module on repository evidence. OQ-01 is dissolved by deferring the runner wiring rather than answered, which is what lets this plan proceed without waiting on `rununify`.

Scope fence: touch ONLY `agent_workflows/host_sandbox_profile.py`, `agent_workflows/cli.py`, `agent_workflows/command_surface.py`, and the new test module. Do NOT create a second capability module. Do NOT edit `host_capability_registry.py`. Do NOT touch `oc_runipd.py` or `agy_runipd.py` (deferred deliberately; touching them re-creates the `rununify` conflict this plan exists to avoid). Do NOT edit `tests/test_host_sandbox_profile.py`, which must stay green unmodified. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do NOT describe this plan as making runs safer: it lands the vocabulary and the checker, and nothing consults them until the follow-up wires the runners. Say so plainly in the terminal history.

Execution contract: commit ONLY the files changed, path-scoped, never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. Several sessions commit to this checkout concurrently.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
