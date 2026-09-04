# IPD: extend the shipped sandbox capability contract with the runner-safety guarantees and a fail-closed action preflight

- Date: 2026-08-30
- Kind: child
- Concern: The runners assume both hosts can do the same things. When that is false the runner asks a host for something it cannot do and the operator gets a confusing downstream failure instead of a clear refusal. The shipped `host_sandbox_profile.HostSandboxCapabilities` already carries a typed, PROBED capability contract for the sandbox/process concerns, but it says nothing about the runner-safety guarantees a lifecycle action actually depends on (commit gateway, deny-push, fresh verifier session), and nothing compares what an ACTION needs against what the host proved it can do.
- Scope: EXTEND the shipped contract in `host_sandbox_profile.py` with the missing runner-safety capabilities and their probes, add an action-to-capability requirement map plus a fail-closed `RUN-HOST-CAPABILITY` preflight, and expose read-only inspection verbs. Excludes creating a second capability module, excludes any change to the skill-delivery registry (`host_capability_registry.py`, a different concern), excludes the sandbox mechanism itself (owned by `1o4eif`), and excludes wiring the preflight into both runner modules (deferred, see OQ-01).
- Scope-Paths: agent_workflows/host_sandbox_profile.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_host_capability_extension.py, tests/test_host_sandbox_profile.py
- Item-Dependencies: none
- Status: approved
- Set: hostcap
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: mjx7ne
- Approval: 2026-08-31, recorded via aw ipd set: status set to approved
- Blocks-Release: next
- From-Backlog: none

## Workflow history
- 2026-08-31 approved (aw set): status set to approved
- 2026-08-31 reviewed (aw set): plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-009. BLOCKING OQ-03 raised.
- 2026-08-31 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-009; NO-GO pending OQ-03. Verified at HEAD `f7a4d53d`. The plan's core judgement HOLDS and is well evidenced: `host_sandbox_profile` is the right owner, the skill-delivery registry is genuinely a different concern, `RUN-HOST-CAPABILITY` greps to 7 in `7f7782` and 0 in the package, `kaygwo`/`k7o7el` reference nothing, and `tests/test_host_sandbox_profile.py` collects 27. TWO problems dominated. (PR-001, HIGH, fixed) This plan REINTRODUCED the exact `## Workflow history` oldest-first defect that PR-006 fixed on its own predecessor `a54m79`, so it arrived failing `aw check plans` with `check.lifecycle-transition-invalid`; reordered newest-first and verified the derived stream is now `draft -> to-review` with 0 findings for this plan. (PR-002, BLOCKER, OPEN) TWO of the three capabilities have NOTHING TO PROBE: `rg 'commit_gateway|deny_push' agent_workflows/` returns ZERO hits and no commit-interception or push-denial enforcement exists; `aw commit`/`offer_commit:133` is a DRIVER-side helper the driver chooses to call, not a boundary an agent cannot evade (spec 25kzda `:773-776` classifies both as Host-dependent). So E-02's "ATTEMPT the thing" has no referent, and an executor would either write the presence-based probe `1o4eif`'s review forbade (the very defect that killed the predecessor) or ship always-False fields while the plan claims a working contract. Raised as blocking OQ-03 with three options and a recommendation; only `supports_fresh_verifier_session` has a real referent today (`agy_verifier.run_fresh_verifier:142`). Also FIXED: (PR-003) the conservative-default guarantee is driven by a LITERAL 7-name `CONTRACT_FIELDS` tuple (`tests/...:41-49`), not introspection, so adding fields left them untested while green - and the plan's "stay green unmodified" instruction FORBADE the fix; scope fence amended for exactly that additive edit and the file added to `Scope-Paths`. (PR-004) `aw host` does not exist (`invalid choice: 'host'`) and `test_command_surface_declarations.py:45` fails CI on any undeclared leaf, so E-06's "check whether a declaration is needed" is answered YES and measured rather than left as a mid-flight discovery. (PR-005) bound E-04/E-05 to spec 25kzda's FOUR action classes and its VERBATIM message at `:534`/`:763` including the recovery command the plan omitted, plus item-local FAIL/cascade/continue and `host_capability_unavailable`. (PR-006) `_run_probe:282` has no injectable runner and the shipped cache has no staleness notion, so E-03 sent the executor after two nonexistent things; recorded the real `_SANDBOX_PROBE_CACHE` seam and its process-global leak hazard. (PR-007) recorded that the chosen owner module itself asserts two capabilities from `host == "opencode"` (`:522-526`) with no probe, so "follow the module's style" must not authorize inspection. (PR-008) added `path:line` anchors. (PR-009) flagged `command_surface.py` contention with approved sibling `0soncw`. Lint conforming at author and review-finalize; `aw check plans` clean for this plan. Five decisions recorded in the typed review record; none irreversible.
- 2026-08-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): SUPERSEDES `a54m79` (detrun-02) at the maintainer's direction. `a54m79` had already been marked "REPLAN - DO NOT EXECUTE" by its own second review, and it blocked four downstream plans by refusing at pre-execution on two unresolved maintainer questions. Both are answered here from repository evidence and recorded in OQ-01/OQ-02. The substance of `a54m79` is PRESERVED, not discarded: its capability vocabulary, its action-requirement idea, and its fail-closed preflight are all real gaps. What changes is the OWNER, from a net-new `host_capabilities.py` to the module that already shipped the same kind of contract.
- 2026-08-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the runner refuse clearly, up front, when a host cannot provide a guarantee the action requires, by extending the capability contract that already exists rather than building a second one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: extend the shipped contract

- [x] E-01 Add the missing runner-safety capability fields to the shipped `HostSandboxCapabilities` dataclass in `host_sandbox_profile.py`. MEASURED starting point, so the executor does not rediscover it: the dataclass today carries `supports_inline_permissions`, `supports_read_only_phase`, `supports_session_resume`, `emits_structured_tool_events`, `emits_child_permission_events`, `supports_process_tree_kill`, `supports_os_sandbox`, `platform`, `sandbox_mechanism`, `probe_notes` (`agent_workflows/host_sandbox_profile.py:134-147`). Add `supports_commit_gateway`, `supports_deny_push`, and `supports_fresh_verifier_session`. Every new field defaults to the CONSERVATIVE value (not-supported), so an unprobed host is treated as lacking the guarantee rather than as having it. Do NOT rename or reorder existing fields: `1o4eif`'s dispatch reads them and its 27 tests pin them.
  ADD THE FIELDS TO THE SHIPPED TEST'S CONTRACT TUPLE TOO (found at review; without this the new fields are structurally invisible to the existing conservative-default guarantee). `tests/test_host_sandbox_profile.py:41-49` defines `CONTRACT_FIELDS` as a literal 7-name tuple and drives BOTH `test_every_capability_defaults_false` (`:84`) and `test_to_dict_snapshots_the_contract` (`:94`) from it. Appending three fields to the dataclass therefore does NOT extend those two guarantees to them; the suite would stay green while asserting nothing about the new fields. Extending that tuple is an EDIT to `tests/test_host_sandbox_profile.py`, which the gate's scope fence otherwise forbids: the fence is hereby AMENDED to permit exactly this additive change (append three names to `CONTRACT_FIELDS`), and nothing else in that file. The "`1o4eif`'s tests pass UNCHANGED" requirement is correspondingly narrowed to "no existing assertion is weakened, removed, or altered". Add the file to `Scope-Paths`.
  - Depends on: none
  - Expected outcome: the extended dataclass carries the three new fields with conservative defaults; `CONTRACT_FIELDS` names all ten so the default-False and to_dict guarantees actually cover the new fields; `1o4eif`'s existing assertions are unweakened and its suite passes; a host descriptor built with no probes reports the new capabilities as unsupported.
  - Execution state: performed

- [x] E-02 Implement probes for the three new capabilities, following the shape the module already uses (`_probe_bwrap`, `_probe_landlock`, `_probe_userns` and the shared `_run_probe` helper at `host_sandbox_profile.py:282`; locate them by symbol). Each probe must ATTEMPT the thing and report what happened rather than inferring from a config file or a version string, which is the discipline the shipped probes already follow. A probe that cannot run reports not-supported, never supported-by-assumption. Record the outcome in the existing `probe_notes` channel rather than adding a second reporting path.
  BLOCKED ON OQ-03 (found at review): for TWO of the three capabilities there is nothing in this repository to probe, so "attempt it and report" has no referent and the only honest verdict a probe could return is not-supported-always. MEASURED: `rg -n 'commit_gateway|deny_push' agent_workflows/` returns ZERO hits, and no commit-interception or push-denial ENFORCEMENT mechanism exists (`rg -n 'intercept|deny.*git commit'` over the package finds nothing relevant; `oc_runipd.py` has no tool-permission deny surface for `git`). Spec 25kzda 5.2 defines these as capabilities of the HOST to prevent the agent from committing except through the engine's gateway and to deny push-capable routes; `git_commit_helper.offer_commit` (`:133`) and `aw commit` are the DRIVER-side path-scoped commit helper, which is a different thing: a helper the driver chooses to use is not a boundary the agent cannot evade. Writing a probe that always returns False, or one that probes `offer_permission`-style helper presence, would be exactly the inspection-not-attempt fail-OPEN pattern `1o4eif`'s review established as forbidden. Only `supports_fresh_verifier_session` has a real referent today (`agy_verifier.run_fresh_verifier:142`, `MODE_FRESH_SESSION:42`, and the distinct-identity enforcement at `:201`). DO NOT invent the enforcement mechanisms inside this plan: that is a large security-boundary design owned elsewhere. Await OQ-03 before implementing the two blocked probes; `supports_fresh_verifier_session` may proceed.
  - Depends on: E-01
  - OQ-03 IS ANSWERED (2026-09-01, maintainer): option (a), KEEP ALL THREE capabilities, honestly labelled. This item is therefore UNBLOCKED, but the answer CONSTRAINS it rather than freeing it. For `commit_gateway` and `deny_push` there is still nothing to attempt (measured: `rg -n 'commit_gateway|deny_push' agent_workflows/` -> 0 hits), so do NOT write a probe for them: declare the fields with `False` defaults plus a `probe_notes` entry stating plainly that no enforcement mechanism exists to probe. A presence-based probe inferring support from `git_commit_helper.offer_commit` is FORBIDDEN - that is the fail-OPEN pattern `1o4eif`'s review established and the exact defect that made the predecessor unexecutable. Only `supports_fresh_verifier_session` gets a real attempt-based probe (`agy_verifier.run_fresh_verifier:142`).
  - Expected outcome: `supports_fresh_verifier_session` has a probe that ATTEMPTS the fresh-session distinction and returns a definite verdict with a note; a probe that raises or times out yields not-supported; no probe reports supported without having observed the behavior. The `commit_gateway` and `deny_push` probes are implemented per OQ-03's answer, or the fields remain declared-and-unprobed (permanently not-supported, which fails closed) with that stated in `probe_notes` rather than papered over.
  - Execution state: performed

- [x] E-03 Add the mock-probe injection seam so degraded, unsupported, and stale-cache host scenarios are testable without owning those hosts. Reuse the module's existing injection style if it has one; the shipped module was written to be testable, so prefer its seam over a new one.
  MEASURED, so the executor does not re-derive it: `_run_probe` (`host_sandbox_profile.py:282`) takes NO injectable runner, it calls `subprocess.run` directly. The seam the shipped tests actually use is the module-level cache plus `force=True`: `tests/test_host_sandbox_profile.py` sets `hsp._SANDBOX_PROBE_CACHE = None` (`:120`, `:135`, `:154`, `:210`) and saves/restores it around each case (`:103`, `:107`). That seam controls the SANDBOX LADDER's cached verdict; it does not generalize to per-capability forcing for the three new fields, because they are not ladder rungs. So a new seam is likely genuinely needed. If you add one, it MUST preserve the module's cache-save/restore discipline so a forced verdict cannot leak into another test (the cache is process-global), and it must not become a way for production code to assert a capability without a probe.
  STALE-CACHE is named in this item but the shipped cache has NO staleness notion (`_SANDBOX_PROBE_CACHE` is a plain per-process memo, `:427`, and TTL/expiry lives in the DIFFERENT skill-delivery registry, `host_capability_registry.EvidenceRecord.is_expired:221`). Either drop "stale-cache" from this item or state exactly what staleness means for a per-process memo; do not import the other module's TTL model by implication.
  - Depends on: E-02
  - Expected outcome: a test can force any capability to any verdict without spawning a real host; a forced verdict is restored after the test so it cannot leak process-globally; the production path is unchanged when no mock is supplied, and the seam cannot be used to claim a capability without a probe.
  - Execution state: performed

### Task group 2: gate the action, not the host

- [x] E-04 Define the action-to-capability requirement map and the checker. An `execute` action needs stronger guarantees than a `review` action, which is the whole point: a review that cannot commit is fine, an execution that cannot route commits through a gateway is not. Implement `check_action_capabilities(...)` returning a definite verdict plus the specific missing capabilities, so the caller can name them. Keep the map DATA, not branching logic, so a reader can see the policy in one place.
  DERIVE THE MAP FROM SPEC 25kzda, DO NOT INVENT IT (added at review; the plan named `execute`/`review` without citing the authority that defines them). The spec's own table is `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:749-754`, keyed by FOUR action classes, not two: read-only classification/skip/check; plan/spec review or IPD authoring; IPD or contract prompt mutation; contractless prompt. Its stated requirement sets name capabilities this dataclass does not have (isolated worktree, path policy, argv capture, timeout/cancel, hook-preserving commit, complete diff capture), and the packet field is `required_host_capabilities` with example values `["isolated_worktree", "commit_gateway", "deny_push"]` (`:912`). So the map MUST state, per action, which spec-named requirements this contract can and CANNOT yet represent, rather than silently narrowing the policy to the three fields being added. A map that omits a required capability it cannot express is a fail-OPEN gate: the action passes because the requirement was never listed.
  - Depends on: E-01
  - Expected outcome: the map states, per action, which capabilities are required, using the spec's action classes and naming the spec-required capabilities this contract cannot yet represent (so the gap is visible instead of silently passing); the checker names every missing capability rather than failing on the first; a fully-capable host passes for every action.
  - Execution state: performed

- [x] E-05 Add the `RUN-HOST-CAPABILITY` finding code and make the check FAIL CLOSED: a missing required capability refuses the action with a message naming the host, the action, and the missing capabilities. This finding code is CONSUMED BY A SIBLING: plan `7f7782` (detrun-05) references `RUN-HOST-CAPABILITY` seven times as one of its 13 deterministic checks, and it is the only downstream plan that depends on this work at all (verified: `kaygwo` and `k7o7el` reference none of this plan's symbols). So the code string and its meaning are a contract with `7f7782`; do not rename it.
  THE MESSAGE IS SPECIFIED VERBATIM BY THE SPEC, so do not compose your own (added at review). Spec 25kzda gives the exact text twice, at `:534` (the 4.2 table) and `:763`:
  `[RUN-HOST-CAPABILITY] Host <host> cannot enforce <capability> required by <item> action <action>. No work started for this item. Choose a capable host or enable and re-probe that capability, then run: aw <host> run <selector>`
  Note it names `<item>` and a RECOVERY COMMAND, which this item's wording omitted; a message missing the recovery command is not spec-conforming. The spec also fixes the ACTION semantics, which this item did not state: FAIL ITEM, cascade dependents, and CONTINUE independent items (`:534`), with outcome `failed` / `host_capability_unavailable` (`:842`, `:972`) and no session started (`:758`). "Refuses the action" is therefore too weak: an item-local failure that lets independent items continue is a different behavior from aborting, and `7f7782` consumes the distinction.
  - Depends on: E-04
  - Expected outcome: an action requiring an unsupported capability is refused item-locally with the spec's VERBATIM message including the recovery command; the outcome is `host_capability_unavailable` and no session starts; a satisfied action proceeds; the finding code is exactly `RUN-HOST-CAPABILITY`.
  - Execution state: performed

- [x] E-06 Add read-only inspection verbs (`aw host probe <host>` and `aw host capabilities [host]`) and `tests/test_host_capability_extension.py`. Tests must cover: the three new fields defaulting conservative; each implemented probe's supported and not-supported paths; the mock seam; the requirement map per action; the fail-closed refusal naming the missing capabilities; and `1o4eif`'s existing sandbox tests still passing.
  THE ANSWER TO "CHECK WHETHER `command_surface.py` REQUIRES A DECLARATION" IS YES, MEASURED (found at review; the item left it as an open lookup, which is how an executor discovers a hard CI failure mid-flight). `aw host` is NOT a command family today: the parser rejects it (`aw host` -> `invalid choice: 'host'`, listing the 40-odd valid families). `COMMAND_INVENTORY` declares 90 leaves across 42 families and `host` is absent. `tests/test_command_surface_declarations.py:45` (`test_zero_undeclared_parser_leaves`) asserts ZERO undeclared leaves via `find_undeclared_leaves(parser)`, so adding a parser leaf WITHOUT a matching `CommandDeclaration` fails CI deterministically. Each declaration requires `command_class`, `human_recipe`, `agent_record_kind`, `mutation_gate`, and an exit contract (`command_surface.py:20-40`); both verbs are reads, so `mutation_gate="none"`.
  CONTENTION WARNING: `command_surface.py` is also in the `Scope-Paths` of APPROVED sibling `0soncw` (runnamecollapse-01), which touches it 11 times to retire the `aw run` group. Re-read the file immediately before editing and verify the staged set, per the gate.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: both verbs work and are read-only (no probe side effects on the repo); each new parser leaf has a matching `CommandDeclaration`; the test module passes; `tests/test_command_surface_declarations.py` and the CLI-conformance matrix pass; `1o4eif`'s tests pass with no assertion weakened.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE CONTRACT ALREADY EXISTS and is the thing to extend. `host_sandbox_profile.HostSandboxCapabilities` is a typed, probe-backed capability descriptor with fail-closed dispatch (`select_execution_profile` raises `HardModeUnavailableError` rather than silently degrading). It shipped with `1o4eif` and carries 27 passing tests.
- THE SKILL REGISTRY IS A DIFFERENT CONCERN, and `a54m79`'s own second review established this after its first review got it wrong. `host_capability_registry.py` is keyed on skill-import tiers (`t1_policy`/`t2_layout`/`t3_global`) with negative-probe classes like `missing_skill` and `stale_adapter`. It is about DELIVERING skills to hosts, not about what a host can guarantee at runtime. Do not fold this work into it and do not treat its existence as making this work redundant.
- The shipped probes ATTEMPT rather than inspect. `_probe_bwrap`, `_probe_landlock`, `_probe_userns` all try the mechanism and report; none infers capability from a version number. E-02 must follow that.
- `probe_notes` already exists as the reporting channel for why a probe concluded what it did. Reuse it.
- Only ONE downstream plan needs this work. Measured across the three: `7f7782` references `RUN-HOST-CAPABILITY` 7 times; `kaygwo` and `k7o7el` reference nothing from this plan. That is why this plan is scoped narrowly and why unblocking it unblocks the chain.
- ADDED AT REVIEW, all measured at HEAD `f7a4d53d`:
  - The shipped tests gate the contract through a LITERAL 7-name tuple, `CONTRACT_FIELDS` (`tests/test_host_sandbox_profile.py:41-49`), not through dataclass introspection. Adding a field does not extend the default-False guarantee to it. See E-01.
  - `_run_probe` has NO injectable runner (`host_sandbox_profile.py:282`). The testing seam the shipped suite uses is the process-global `_SANDBOX_PROBE_CACHE` memo with save/restore. See E-03.
  - The shipped `detect_host_capabilities` asserts two capabilities from HOST IDENTITY rather than from a probe: `host == "opencode"` sets `emits_structured_tool_events` and `supports_session_resume` to True with only a code comment as evidence (`:522-526`). That is inspection, not attempt, in the module this plan extends. Do NOT copy the pattern for the new fields, and do NOT quietly rely on it: a `review` action requiring argv capture would pass on a host that merely calls itself opencode.
  - `supports_inline_permissions` and `emits_child_permission_events` are declared but NEVER set anywhere in the package (`rg` finds only the two dataclass lines). Precedent exists for a declared-and-unprobed field, which is safe only because the default is False. E-02's fallback relies on the same property.
  - `aw host` does not exist and `command_surface.COMMAND_INVENTORY` declares 90 leaves in 42 families, none named `host`; `tests/test_command_surface_declarations.py:45` fails CI on any undeclared leaf. See E-06.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `a54m79` Goal section | The superseded plan had ALREADY been marked unexecutable by its own reviewer: its Goal opens `REPLAN - DO NOT EXECUTE`. It nonetheless sat `approved` and was launched, refusing at pre-execution and cascading four dependents to `dependency-blocked`. A plan that knows it must be replanned should not have been approved; that is a process gap worth noting separately from this plan's content. | the plan file's own Goal text; run-20260830T202022Z-3475919 showing `a54m79` blocked in 1s and 4 items cascading |
| F2 | HIGH | `host_sandbox_profile.py` | The overlap that motivated superseding: the shipped module already provides the typed capability descriptor, the probe pattern, and fail-closed dispatch. `a54m79` would have created `host_capabilities.py` with `HostCapability`/`CapabilityAssurance`/`HostCapabilityDescriptor`, a parallel vocabulary for the same guarantees. | `HostSandboxCapabilities` field list and `select_execution_profile` / `detect_host_capabilities` / `HardModeUnavailableError` read at HEAD |
| F3 | MED | `a54m79` vs `host_capability_registry.py` | The overlap is PARTIAL, not total, and this correction matters because it is why the work survives at all. The skill-delivery registry does NOT cover commit-gateway, deny-push, or fresh-verifier-session. Those are genuine gaps `a54m79` identified correctly. Discarding the plan wholesale would have lost real findings. | `a54m79`'s pass-2 review text correcting its own pass-1 "already shipped" claim; the registry's tier/probe vocabulary |
| F4 | MED | `7f7782` | `RUN-HOST-CAPABILITY` is a CROSS-PLAN CONTRACT, not an internal name. `7f7782` cites it 7 times as one of 13 deterministic checks and states the code greps to zero today. Renaming it would silently break that plan. | `grep -c RUN-HOST-CAPABILITY` in `7f7782` = 7; zero occurrences in the package |
| F5 | LOW | `kaygwo`, `k7o7el` | Neither references any symbol from this work, so their `dependency-blocked` status was purely transitive through `a54m79`. Landing this plan unblocks the chain without either needing anything from it. | grep for this plan's symbols in both files returned nothing |
| F6 | BLOCKER | `agent_workflows/` (absence) | TWO of the three capabilities have NOTHING TO PROBE. `commit_gateway` and `deny_push` name host ENFORCEMENT (spec 25kzda 5.2: the agent cannot commit except through the engine's gateway; push-capable routes are denied) and no such enforcement exists here. `aw commit`/`offer_commit` is a driver-side helper the driver chooses to call, not a boundary the agent cannot evade, so probing for it would report a guarantee the host does not provide. An always-False probe is honest but makes the field decorative; a presence-based probe is the fail-OPEN pattern `1o4eif`'s review forbade. Escalated as blocking OQ-03. | `rg -n 'commit_gateway\|deny_push' agent_workflows/` -> 0 hits; no commit-interception or push-denial mechanism in the package; `git_commit_helper.offer_commit:133`; spec `:773-776` classifies both as Host-dependent |
| F7 | HIGH | `.aw/records/plans/pending/...mjx7ne...ipd.md:18-21` (as authored) | The plan's own `## Workflow history` was ordered OLDEST-FIRST, so `ipd_lifecycle._plan_status_events` (which reverses, assuming newest-first) derived the event stream `to-review -> draft` and `aw check plans` reported `check.lifecycle-transition-invalid` against this plan. This is the SAME defect PR-006 fixed on the predecessor `a54m79`, reintroduced by the successor. | `aw check plans --agent` at pre-review HEAD listed this plan under `check.lifecycle-transition-invalid`; after the fix its finding count is 0 |
| F8 | HIGH | `tests/test_host_sandbox_profile.py:41-49` | The conservative-default guarantee is driven by a LITERAL 7-name tuple, not by introspecting the dataclass, so adding three fields leaves them untested while the suite stays green. The plan's "tests pass UNCHANGED" instruction actively forbade the edit that closes this. | `CONTRACT_FIELDS` literal at `:41`; consumed at `:84` and `:94` |
| F9 | MED | spec `:749-754`, `:534`, `:763` | The plan invented a two-action vocabulary (`execute`/`review`) and paraphrased the refusal message. The spec fixes FOUR action classes, an exact verbatim message including a recovery command, and item-local FAIL-plus-cascade semantics. Paraphrase breaks the contract `7f7782` consumes. | spec action table `:749-754`; message `:534` and `:763`; outcome `host_capability_unavailable` `:842`, `:972` |
| F10 | MED | `host_sandbox_profile.py:522-526` | The module this plan extends already asserts two capabilities from HOST IDENTITY (`host == "opencode"`) with no probe, contradicting the attempt-not-inspect discipline the same module's docstring publishes. Extending this module inherits the inconsistency, so the plan must not treat "follow the module's existing style" as sufficient. | `caps.emits_structured_tool_events = True` under `if host == "opencode"` with only a comment as evidence |

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
- Under-scope, NOT deliberate, ESCALATED (added at review): two of the three capabilities cannot be probed because the enforcement they describe does not exist in this repository (F6, OQ-03). The plan as authored would have produced two fields that can only ever read not-supported, which then makes the E-04 map refuse EVERY action that requires them. That is fail-closed and therefore safe, but it is not what the plan claims, and building the enforcement is a separate security-boundary design this plan must not absorb.
- Scope-Paths GREW at review to include `tests/test_host_sandbox_profile.py`, for the single additive `CONTRACT_FIELDS` change E-01 now requires (F8). Without it the new fields carry no default-False guarantee.
- `cli.py` is heavily contended in this repo. Re-read it immediately before editing and verify the staged set before committing. `command_surface.py` is contended too: approved sibling `0soncw` declares it and touches it 11 times.

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
- Resolution or deferral rationale: `host_sandbox_profile.py`, the module that already shipped with `1o4eif`. (Review note: this remains the right owner, but see OQ-03 and F10 - the chosen module is not itself fully faithful to the attempt-not-inspect rule, so "match the module's style" is not a sufficient instruction.) Resolved from repository evidence at the maintainer's direction. It already provides exactly this KIND of thing: a typed dataclass of capabilities, probes that attempt rather than infer, a `probe_notes` reporting channel, and fail-closed dispatch that raises rather than degrading silently. Building `a54m79`'s parallel `host_capabilities.py` would have produced two vocabularies for one concept, which is the duplication this repo repeatedly pays for (compare `dhuape`, `rununify`). Note the boundary carefully, because the superseded plan's first review got it wrong: the SKILL-DELIVERY registry `host_capability_registry.py` is a different concern and is NOT the owner either (F3).

### OQ-03: Two of the three capabilities have no enforcement to probe. Declare them unprobed, or build the enforcement?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-002
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER (2026-09-01): option (a), KEEP ALL THREE
  CAPABILITIES, HONESTLY LABELLED. Declare `commit_gateway` and `deny_push` with `False` defaults and a
  `probe_notes` entry recording that no enforcement exists to probe, alongside the one capability that
  does have a real referent (`supports_fresh_verifier_session`). Option (b) stays REJECTED (it is a
  security-boundary design of `1o4eif` magnitude, far outside a 6-item plan), and option (c) - narrowing
  the plan to the single probeable capability - was CONSIDERED AND DECLINED.
  WHY (a) RATHER THAN THE REVIEW'S PREFERRED (c), which is the substance of the ruling and the reason
  the review's own recommendation was overturned: the review argued (c) is "cleaner because it does not
  ship two fields that can never read supported". That reasoning applies a SECURITY standard, under
  which a guarantee an adversary can evade is worthless. The maintainer's threat model here is ACCIDENT
  PREVENTION, not adversarial defense: agents in this repo act on trained reflex (a solo-repo agent is
  strongly trained that `git add -A` is correct), and this repo asks for something "not in their
  nature". Under that model a declared-but-unenforced capability is NOT worthless, because a guard that
  refuses and says "use `aw commit` instead" would very likely stop the accidental case even though a
  determined process could bypass it. Bypassability is therefore a FEATURE against accidents, not a
  disqualification.
  WHAT THIS OBLIGES THE EXECUTOR TO DO, so (a) does not become the fail-OPEN pattern `1o4eif`'s review
  forbade: the two unenforced fields MUST default `False`, MUST carry a `probe_notes` string saying
  plainly that no enforcement mechanism exists to probe (measured: `rg -n 'commit_gateway|deny_push'
  agent_workflows/` returns ZERO hits), and MUST NOT be satisfied by a presence-based probe. A probe
  that infers support from the existence of `git_commit_helper.offer_commit` would be exactly the
  fail-OPEN defect that made the predecessor unexecutable; `offer_commit` is a helper the DRIVER chooses
  to call, not a boundary an agent cannot evade, and spec `25kzda` `:773-776` already classifies both
  guarantees as Host-dependent for that reason.
  ACCEPTED CONSEQUENCE, stated rather than hidden: because both fields read `False` on every host today,
  the E-04 requirement map will refuse `execute` wherever it requires them. That is fail-CLOSED and
  correct, and it means the gate is honest-but-inert until enforcement lands. The plan must not claim a
  working capability contract for those two; it ships a truthful declaration plus an accident-guard, and
  the enforcement itself is a separate, later piece of work.
  SUPERSEDED REASONING, preserved so the decision is auditable rather than silently rewritten: the repository cannot answer it because the answer is a scope and risk call, not a fact. MEASURED (F6): `commit_gateway` and `deny_push` describe HOST ENFORCEMENT per spec 25kzda 5.2 (the agent cannot commit except through the engine's gateway; push-capable routes are denied and remote credentials withheld), and `rg -n 'commit_gateway|deny_push' agent_workflows/` returns ZERO hits with no interception or denial mechanism anywhere in the package. What DOES exist is `git_commit_helper.offer_commit` (`:133`) and `aw commit`, a driver-side path-scoped commit helper that never passes `--no-verify` and never pushes. That is a helper the DRIVER chooses to call; it is not a boundary an agent cannot evade, and spec `:773-776` classifies both guarantees as Host-dependent precisely because they need controlled execution rather than good behavior. So a probe has no referent. The three candidate answers differ materially:
  (a) DECLARE UNPROBED. Add both fields with False defaults and a `probe_notes` entry saying no enforcement exists to probe. Every action requiring them then refuses, which is fail-CLOSED and safe, and matches the existing precedent of `supports_inline_permissions` (declared, never set). Cost: the E-04 map refuses `execute` on every host, so the gate is correct but useless until enforcement lands, and this plan's stated goal is only half met.
  (b) BUILD THE ENFORCEMENT HERE. Add commit interception and push denial. This is a security-boundary design of the same magnitude as `1o4eif` itself, far outside a 6-item plan, and would collide with the runner modules this plan deliberately refuses to touch.
  (c) NARROW THE PLAN to `supports_fresh_verifier_session`, the one capability with a real referent today (`agy_verifier.run_fresh_verifier:142`, `MODE_FRESH_SESSION:42`, distinct-identity enforcement at `:201`), and hand the other two to a follow-up that owns the enforcement.
  RECOMMENDATION: (a) or (c). Both are honest and fail closed; (c) is cleaner because it does not ship two fields that can never read supported. Do NOT choose (b) inside this plan.
  CONSEQUENCE IF UNRESOLVED: an executor either invents a presence-based probe (the fail-OPEN pattern `1o4eif`'s review established as forbidden, and the exact defect that made the predecessor unexecutable) or silently ships always-False fields while the plan claims a working capability contract.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the extended dataclass showing the three new fields and their conservative defaults. Paste a descriptor built with NO probes showing all three reporting unsupported. Paste the extended `CONTRACT_FIELDS` tuple showing all TEN names, and paste `test_every_capability_defaults_false` output proving it now subtests the three new fields by name (a run that does not name them has not validated this item, per F8). Paste `tests/test_host_sandbox_profile.py` passing, and paste a `git diff` of that file proving the ONLY change is the additive tuple extension with no existing assertion weakened or removed.
  - Observed evidence: ALL AT HEAD `80fa5441c7112134efc2f5b9a75c80904300c857 (the frozen begin-receipt base; the work is committed as `30108f78`, and every measurement above was re-run at that commit with an IDENTICAL result)` (`git rev-parse HEAD`).
    (1) THE EXTENDED DATACLASS, three new fields, conservative defaults (`host_sandbox_profile.py`):
    ```
        supports_commit_gateway: bool = False
        supports_deny_push: bool = False
        supports_fresh_verifier_session: bool = False
    ```
    (2) A DESCRIPTOR BUILT WITH NO PROBES reports all three unsupported (`HostSandboxCapabilities().to_dict()`):
    ```
    supports_commit_gateway         false
    supports_deny_push              false
    supports_fresh_verifier_session false
    ```
    (3) THE EXTENDED `CONTRACT_FIELDS`, all TEN names (`tests/test_host_sandbox_profile.py:41-56`):
    `supports_inline_permissions`, `supports_read_only_phase`, `supports_session_resume`,
    `emits_structured_tool_events`, `emits_child_permission_events`, `supports_process_tree_kill`,
    `supports_os_sandbox`, `supports_commit_gateway`, `supports_deny_push`,
    `supports_fresh_verifier_session`.
    (4) PROOF THE GUARANTEE NOW SUBTESTS THE NEW FIELDS BY NAME. Note the shipped test is named
    `test_every_contract_field_exists_and_defaults_false` (the plan called it
    `test_every_capability_defaults_false`; same test, `:82`), and a PASSING `subTest` prints nothing, so
    "names them" cannot be shown by a green run. Demonstrated by FALSIFICATION instead: temporarily
    flipping the two unenforced defaults to `True` in the dataclass (the fail-OPEN direction) makes the
    guarantee bite and NAME the field, after which the flip was reverted:
    ```
    E  AssertionError: True is not False : supports_commit_gateway must default False so an
       unprobed host claims nothing
    1 failed, 1 passed in 0.17s
    ```
    Reverted and re-run green: `27 passed in 0.49s`.
    (5) `tests/test_host_sandbox_profile.py` PASSING, UNCHANGED COUNT
    (`python3 -m pytest tests/test_host_sandbox_profile.py -o addopts="" -q`):
    ```
    ...........................                                              [100%]
    27 passed in 0.52s
    ```
    (6) `git diff tests/test_host_sandbox_profile.py` proving the ONLY change is the additive tuple
    extension, with NO existing assertion weakened, removed, or altered (the whole diff, verbatim):
    ```
    @@ -46,6 +46,13 @@ CONTRACT_FIELDS = (
         "emits_child_permission_events",
         "supports_process_tree_kill",
         "supports_os_sandbox",
    +    # mjx7ne E-01: the runner-safety capabilities. Appended here because this tuple - not
    +    # dataclass introspection - drives `test_every_contract_field_exists_and_defaults_false`
    +    # and `test_to_dict_snapshots_the_contract`, so a field absent from it carries NO
    +    # default-False or snapshot guarantee while the suite stays green.
    +    "supports_commit_gateway",
    +    "supports_deny_push",
    +    "supports_fresh_verifier_session",
     )
    ```
    (7) NO EXISTING FIELD RENAMED OR REORDERED: pinned by
    `test_the_shipped_sandbox_fields_are_neither_renamed_nor_reordered` (new module), which asserts the
    first seven dataclass fields by exact name and order.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: for each probe you IMPLEMENTED, paste a supported and a not-supported outcome with the `probe_notes` text, plus a probe that raises or times out yielding not-supported. Show that no probe returns supported without an observation by pasting the code path rather than asserting it. For any capability left unprobed under OQ-03, paste the field defaulting False AND the `probe_notes` entry stating it is declared-and-unprobed; do NOT paste a placeholder probe. STATE EXPLICITLY which of the three you implemented and why, and do not claim a guarantee for one you did not.
  - Observed evidence: WHICH OF THE THREE I IMPLEMENTED, STATED EXPLICITLY: exactly ONE,
    `supports_fresh_verifier_session`. The other two, `supports_commit_gateway` and
    `supports_deny_push`, are DECLARED AND NOT PROBED per OQ-03's answer (option (a)), because the
    enforcement they name does not exist in this repository so there is nothing to attempt. I claim NO
    guarantee for those two: they read not-supported on every host. Re-measured at this HEAD,
    `rg -n 'commit_gateway|deny_push' agent_workflows/` returns hits ONLY in the two files this plan
    authored (`host_sandbox_profile.py` declaring and explaining them, `host_cmd.py` reporting them) and
    nothing resembling a commit-interception or push-denial mechanism.
    (1) `supports_fresh_verifier_session` SUPPORTED, with its `probe_notes` text:
    ```
    supports_fresh_verifier_session: True
    note: fresh-verifier separation enforced: a distinct-identity run finalized and a
          reused-identity run was REFUSED (executor='agy-executor-fe55cfeb90189c1f',
          verifier='agy-verifier-a263de56d36e3784')
    ```
    (2) NOT-SUPPORTED PATH, a probe that RAISES yields not-supported (never supported-by-assumption):
    ```
    False | probe raised RuntimeError: simulated probe failure
    ```
    (3) NOT-SUPPORTED PATH, the FAIL-OPEN case: a fresh-verifier contract that ACCEPTS a reused session
    identity must NOT report supported. Exercised by
    `test_fresh_verifier_probe_requires_the_reused_identity_to_be_REFUSED`, which patches the collision
    guard away (exactly the defect) and asserts the probe reports False with `"reused session identity"`
    in the note.
    (4) NO PROBE RETURNS SUPPORTED WITHOUT AN OBSERVATION - the CODE PATH, not an assertion. In
    `_probe_fresh_verifier_session` the ONLY `return (True, ...)` sits inside
    `except _agy.SessionIdentityCollisionError:`, i.e. reachable ONLY after the distinct-identity run
    already produced `is_authoritative and can_finalize` AND the same-identity run was actually refused:
    ```
            except _agy.SessionIdentityCollisionError:
                return (
                    True,
    ```
    Every other exit returns False, including the outer `except Exception` (`# a probe never propagates;
    unknown => not supported`).
    (5) THE TWO UNPROBED CAPABILITIES: field defaulting False AND the `probe_notes` entry saying so. No
    placeholder probe exists - `_RUNNER_SAFETY_PROBES` maps both names to `None`, asserted by
    `test_the_two_unenforced_capabilities_are_declared_and_not_probed`:
    ```
    supports_commit_gateway: False
    note: DECLARED, NOT PROBED: no commit-interception enforcement exists in this package to
          attempt, so this capability is permanently not-supported (fail-closed).
          `git_commit_helper.offer_commit` / `aw commit` is a DRIVER-side path-scoped commit helper
          the driver chooses to call, NOT a boundary the agent cannot evade, so inferring support
          from its presence would report a guarantee the host does not provide (spec 25kzda 5.2
          guarantee 2, classified Host-dependent).

    supports_deny_push: False
    note: DECLARED, NOT PROBED: no push-denial enforcement (tool/network/credential denial) exists
          in this package to attempt, so this capability is permanently not-supported
          (fail-closed). The driver not pushing is a driver behavior, not a host-enforced denial
          (spec 25kzda 5.2 guarantee 1, classified Host-dependent).
    ```
    (6) THE FORBIDDEN PRESENCE-BASED PROBE IS STRUCTURALLY EXCLUDED:
    `test_no_runner_safety_probe_infers_support_from_helper_presence` asserts the module never imports
    `git_commit_helper` / `offer_commit`; both appear only in explanatory prose, never in code that
    decides a verdict.
    (7) REPORTING CHANNEL REUSED, not duplicated: every verdict lands in the existing `probe_notes` dict
    (`detect_host_capabilities` does `caps.probe_notes.update(notes)`), pinned by
    `test_detect_host_capabilities_records_the_probe_notes`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a test forcing a capability to each verdict via the mock seam. State whether you reused `_SANDBOX_PROBE_CACHE`-style save/restore or added a new seam, and if added, why the existing one did not fit. Paste evidence a forced verdict does NOT leak into a subsequent test (the cache is process-global), for example the same capability reading its real value in a later case. Paste evidence the production path is unchanged with no mock supplied. State what you did with the "stale-cache" scenario, given the shipped memo has no staleness notion.
  - Observed evidence: SEAM CHOICE, STATED. I ADDED a new seam, `_FORCED_RUNNER_SAFETY` plus the
    `forced_runner_safety_verdicts` context manager, and reused the shipped module's STYLE (a
    module-level global that tests save and restore) rather than its instance. WHY THE EXISTING ONE DID
    NOT FIT, as the plan's E-03 note predicted: the shipped seam is `_SANDBOX_PROBE_CACHE` + `force=True`,
    which caches the SANDBOX LADDER's single verdict (`(mechanism, notes)`); the three new capabilities
    are not ladder rungs and have no per-capability representation in that tuple, so it cannot force them.
    The new seam keeps the same save/restore discipline and goes further: restoration happens in
    `__exit__`, so a forced verdict cannot leak even when the test body RAISES (pinned by
    `test_the_seam_is_restored_even_when_the_body_raises`).
    (1) FORCING EACH VERDICT, both directions:
    ```
    real:         {'supports_commit_gateway': False, 'supports_deny_push': False,
                   'supports_fresh_verifier_session': True}
    forced FALSE: False | FORCED VERDICT (test seam): forced not-supported
    forced TRUE:  True  | FORCED VERDICT (test seam): forced supported
    ```
    A forced verdict is LABELLED `FORCED VERDICT (test seam)` in `probe_notes`, so a forced run can never
    be mistaken for a probed one in a report.
    (2) NO LEAK (the seam is process-global). Same process, after the context exits, the capability reads
    its REAL value again:
    ```
    after (no leak): {'supports_commit_gateway': False, 'supports_deny_push': False,
                      'supports_fresh_verifier_session': True}
    ```
    Pinned by `test_a_forced_verdict_does_not_leak_out_of_the_context`, which additionally asserts the
    real note (`DECLARED, NOT PROBED`) is back.
    (3) PRODUCTION PATH UNCHANGED WITH NO MOCK SUPPLIED: `hsp._FORCED_RUNNER_SAFETY` is `None` by default
    (asserted by `test_the_production_path_is_unchanged_with_no_mock_supplied`), and
    `probe_runner_safety_capabilities` consults it only when it is not `None`:
    ```
    seam default: None
    ```
    (4) THE SEAM CANNOT CLAIM A CAPABILITY WITHOUT A PROBE IN PRODUCTION: it is consulted only by
    `probe_runner_safety_capabilities`, and `check_action_capabilities` is PURE over the descriptor it is
    handed, so a forced verdict cannot change a checker answer for a descriptor built without it
    (`test_the_checker_runs_no_probe`).
    (5) "STALE-CACHE", AS THE REVIEW REQUIRED ME TO STATE: DROPPED, deliberately, with the reason recorded
    in the code. These probes are NOT CACHED AT ALL (`probe_runner_safety_capabilities` recomputes on
    every call), so there is no memo that could go stale. I did not import the TTL model from
    `host_capability_registry.EvidenceRecord.is_expired`, which belongs to the different skill-delivery
    concern; the shipped `_SANDBOX_PROBE_CACHE` likewise has no staleness notion, and the docstring says
    so explicitly so a later reader does not assume one.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the requirement map showing it is DATA. Paste the checker naming MULTIPLE missing capabilities in one verdict, not just the first. Paste a fully-capable host passing every action. Paste the map alongside spec `:749-754` showing the action classes MATCH the spec's four, and showing which spec-required capabilities this contract cannot yet represent are explicitly recorded rather than omitted.
  - Observed evidence: measured at HEAD `80fa5441c7112134efc2f5b9a75c80904300c857 (the frozen begin-receipt base; the work is committed as `30108f78`, and every measurement above was re-run at that commit with an IDENTICAL result)`.
    (1) THE MAP IS DATA - a `Dict[str, ActionRequirement]` of frozen dataclasses, no branching, one place
    a reader sees the whole policy (`ACTION_CAPABILITY_REQUIREMENTS`):
    ```
    read_only:           required=[]
                         unrepresented=['complete_diff_capture']
    review:              required=['supports_commit_gateway', 'supports_deny_push',
                                   'supports_fresh_verifier_session']
                         unrepresented=['isolated_worktree', 'path_policy', 'argv_capture',
                                        'timeout_cancel', 'hook_preserving_commit']
    mutate:              required=['supports_commit_gateway', 'supports_deny_push',
                                   'supports_fresh_verifier_session']
                         unrepresented=['isolated_worktree', 'path_policy', 'argv_capture',
                                        'timeout_cancel', 'hook_preserving_commit',
                                        'complete_diff_capture']
    contractless_prompt: required=['supports_commit_gateway', 'supports_deny_push']
                         unrepresented=['isolated_worktree', 'path_policy',
                                        'complete_diff_capture']
    ```
    (2) THE ACTION CLASSES MATCH THE SPEC'S FOUR, beside spec `:749-754`. Spec rows, in order:
    "Read-only classification/skip/check" -> `read_only`; "Plan/spec review or IPD authoring" -> `review`;
    "IPD or contract prompt mutation" -> `mutate`; "Contractless prompt" -> `contractless_prompt`. Four
    spec rows, four map keys, asserted by `test_the_map_uses_the_specs_four_action_classes`. The plan's
    own draft vocabulary (`execute`/`review`) was NOT used; `check_action_capabilities("execute", ...)`
    deliberately RAISES `UnknownActionError` rather than defaulting, because defaulting is how a mutating
    action inherits the read-only policy (`test_an_unknown_action_raises_rather_than_defaulting`).
    (3) SPEC-REQUIRED CAPABILITIES THIS CONTRACT CANNOT REPRESENT ARE RECORDED, NOT OMITTED. The spec
    names eight for review; three are representable here and the other five are carried in
    `unrepresented` with a prose reason in `UNREPRESENTED_SPEC_CAPABILITIES`. Every `unrepresented` name
    is asserted to resolve to a recorded gap (`test_every_unrepresented_name_resolves_to_a_recorded_gap`),
    so a typo cannot silently DROP a requirement - which would be fail-OPEN, since an unlisted
    requirement can never fail. The verbs print them (`not representable by this contract: ...`), so the
    gap is visible to an operator too.
    (4) THE CHECKER NAMES MULTIPLE MISSING CAPABILITIES IN ONE VERDICT, not just the first
    (all-unsupported host, `review`):
    ```
    satisfied: False missing: ['supports_commit_gateway', 'supports_deny_push',
                               'supports_fresh_verifier_session']
    ```
    (5) A FULLY-CAPABLE HOST PASSES EVERY ACTION:
    ```
    read_only -> True
    review -> True
    mutate -> True
    contractless_prompt -> True
    ```
    (6) THE VERDICT CARRIES ITS EVIDENCE: each missing capability's `probe_notes` entry is attached
    (`test_the_verdict_carries_the_evidence_for_each_missing_capability`), so a refusal explains itself.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the refusal for a host missing a required capability, and paste it BESIDE spec `:763` proving the message is the spec's VERBATIM text including `<item>` and the `aw <host> run <selector>` recovery command. Paste the same action PROCEEDING when the capability is supported; a one-sided demonstration does not show a gate. Paste evidence the refusal is ITEM-LOCAL (outcome `host_capability_unavailable`, dependents cascade, an independent item continues) rather than a whole-run abort. Paste a grep proving the finding code string is exactly `RUN-HOST-CAPABILITY`.
  - Observed evidence: measured at HEAD `80fa5441c7112134efc2f5b9a75c80904300c857 (the frozen begin-receipt base; the work is committed as `30108f78`, and every measurement above was re-run at that commit with an IDENTICAL result)`.
    (1) THE REFUSAL, for a host missing a required capability (`mutate`, gateway unsupported):
    ```
    ok: False | outcome: failed | reason: host_capability_unavailable
    session_started: False | cascade_dependents: True | aborts_run: False
    [RUN-HOST-CAPABILITY] Host opencode cannot enforce supports_commit_gateway required by
    mjx7ne action mutate. No work started for this item. Choose a capable host or enable and
    re-probe that capability, then run: aw opencode run mjx7ne
    ```
    (2) THE MESSAGE IS THE SPEC'S VERBATIM TEXT, compared BESIDE spec `:763` by byte equality, not
    paraphrase. The test transcribes the spec line independently, so the comparison is against the SPEC
    and not against the implementation (`test_the_message_matches_the_specs_verbatim_text`):
    ```
    spec  : [RUN-HOST-CAPABILITY] Host <host> cannot enforce <capability> required by <item> action <action>. No work started for this item. Choose a capable host or enable and re-probe that capability, then run: aw <host> run <selector>
    ours  : [RUN-HOST-CAPABILITY] Host <host> cannot enforce <capability> required by <item> action <action>. No work started for this item. Choose a capable host or enable and re-probe that capability, then run: aw <host> run <selector>
    EQUAL : True
    ```
    It carries BOTH things the plan's own wording had omitted: the `<item>` slot
    (`required by mjx7ne action mutate`) and the RECOVERY COMMAND (`then run: aw opencode run mjx7ne`).
    (3) THE SAME ACTION PROCEEDING when the capability is supported - the other half of the gate, so this
    is not a one-sided demonstration:
    ```
    ok: True | message: '' | outcome: ''
    ```
    (4) THE REFUSAL IS ITEM-LOCAL, NOT A RUN ABORT (spec 4.2: FAIL ITEM; cascade dependents; continue
    independent items). Outcome `failed` / `host_capability_unavailable`, `session_started=False`,
    `mutated=False`, `cascade_dependents=True`, `aborts_run=False`. Shown concretely, one item refused
    while an INDEPENDENT item on the SAME incapable host still passes:
    ```
    blocked1     ok: False  cascade: True  aborts_run: False
    independent1 ok: True
    ```
    A refusal is also a recordable OUTCOME rather than an exception, so a driver can log it
    (`test_the_preflight_does_not_raise_for_an_unmet_requirement`).
    (5) THE FINDING CODE STRING IS EXACTLY `RUN-HOST-CAPABILITY`, the cross-plan contract with
    `7f7782`/`wlxkoz`, not renamed:
    ```
    $ rg -o 'RUN_HOST_CAPABILITY = "[^"]*"' agent_workflows/host_sandbox_profile.py
    RUN_HOST_CAPABILITY = "RUN-HOST-CAPABILITY"
    $ rg -c 'RUN-HOST-CAPABILITY' agent_workflows/host_sandbox_profile.py
    6
    ```
    (6) A REAL HOST TODAY REFUSES THE MUTATING ACTIONS, which is OQ-03's ACCEPTED CONSEQUENCE asserted
    rather than assumed (`test_a_real_host_today_refuses_the_mutating_actions`): the missing set is exactly
    `{supports_commit_gateway, supports_deny_push}`. Fail-CLOSED and correct.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste both verbs' output and evidence they are read-only (`git status --porcelain` showing no new entry authored by you). Paste the new test module passing. Paste `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` PASSING, which is the check that fails on an undeclared leaf; paste the `CommandDeclaration` entries you added. Paste the CLI-conformance matrix passing, or attribute pre-existing failures BY NAME and prove this family is not among them.
  - Observed evidence: measured at HEAD `80fa5441c7112134efc2f5b9a75c80904300c857 (the frozen begin-receipt base; the work is committed as `30108f78`, and every measurement above was re-run at that commit with an IDENTICAL result)`.
    (1) `aw host capabilities opencode` OUTPUT, abridged to the runner-safety rows and the action
    verdicts (full text reproducible with the same command):
    ```
    host opencode  platform=linux  sandbox_mechanism=landlock
      NO   supports_commit_gateway (runner-safety)
           why: DECLARED, NOT PROBED: no commit-interception enforcement exists ...
      NO   supports_deny_push (runner-safety)
           why: DECLARED, NOT PROBED: no push-denial enforcement ...
      yes  supports_fresh_verifier_session (runner-safety)
           why: fresh-verifier separation enforced: a distinct-identity run finalized and a
                reused-identity run was REFUSED (...)
      actions:
        ALLOWED  read_only
                 not representable by this contract: complete_diff_capture
        REFUSED  review  missing: supports_commit_gateway, supports_deny_push
                 not representable by this contract: isolated_worktree, path_policy,
                 argv_capture, timeout_cancel, hook_preserving_commit
        REFUSED  mutate  missing: supports_commit_gateway, supports_deny_push
        REFUSED  contractless_prompt  missing: supports_commit_gateway, supports_deny_push

    1 host(s) reported; 3 (host, action) pair(s) refused
    ```
    (2) `aw host probe opencode --agent` emits schema-conforming `aw.agent/v1` JSONL and exits 0:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"host probe","outcome":"clean","exit":0,
     "verified":true,"complete":true,"target":"opencode","findings":0,
     "evidence":["opencode"],"next":null}
    ```
    (3) EXIT CONTRACT `(0, 2)` MEASURED: `host probe opencode` -> 0; `host capabilities --json` -> 0; bare
    `aw host` (missing subcommand) -> 2; `host capabilities --badflag` -> 2.
    (4) READ-ONLY: `git status --porcelain` is BYTE-IDENTICAL before and after running BOTH verbs. The six
    entries listed are this plan's own edits; the verbs added none:
    ```
     M agent_workflows/cli.py
     M agent_workflows/command_surface.py
     M agent_workflows/host_sandbox_profile.py
     M tests/test_host_sandbox_profile.py
    ?? agent_workflows/host_cmd.py
    ?? tests/test_host_capability_extension.py
    ```
    Additionally `test_the_verbs_write_nothing_to_the_repository` spies on `builtins.open` and asserts
    ZERO paths were opened for writing. HONEST CAVEAT, recorded in the module docstring and the help
    epilog: `host probe` DOES execute probes, and the sandbox probe builds and removes a real jail in a
    temporary directory, so it is REPOSITORY-read-only rather than side-effect-free.
    (5) THE `CommandDeclaration` ENTRIES ADDED (`command_surface.py`), both reads, `mutation_gate="none"`,
    `exit_contract=(0, 2)` deliberately excluding 1 (a not-supported capability is an ANSWER, not a
    finding, and claiming exit 1 would oblige a `domain_failure` scenario these printers cannot produce):
    ```
    CommandDeclaration(command="host probe",        command_class="read",
        human_recipe="detail", agent_record_kind="result", mutation_gate="none",
        empty_error_renderer="renderer_boundary", legacy_flags=("--agent", "--json"),
        exit_contract=(0, 2))
    CommandDeclaration(command="host capabilities", command_class="read",
        human_recipe="detail", agent_record_kind="result", mutation_gate="none",
        empty_error_renderer="renderer_boundary", legacy_flags=("--agent", "--json"),
        exit_contract=(0, 2))
    ```
    (6) THE NEW TEST MODULE PASSES
    (`python3 -m pytest tests/test_host_capability_extension.py -o addopts="" -q`):
    ```
    ................................................                         [100%]
    48 passed in 0.29s
    ```
    Together with the shipped module: `75 passed in 0.78s`.
    (7) `test_zero_undeclared_parser_leaves` AND THE CLI-CONFORMANCE MATRIX WERE ALREADY FAILING AT MY
    BASELINE, and I attribute that BY NAME rather than claim a pass I did not get. Measured at the SAME
    HEAD `80fa5441` with my changes STASHED, four tests fail identically before and after:
    `test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`,
    `::test_empty_error_renderer_classification_consistency`,
    `test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves`, and
    `::test_every_declared_leaf_gets_a_full_scenario_row_set` (`4 failed, 14 passed` both with and without
    my changes). PROOF THIS FAMILY IS NOT AMONG THE CAUSES: the undeclared set is 63 leaves before my
    change and 64 after (`__complete`, `pwatch`, the whole `config`/`conf`/`oc`/`agy` verb families, the
    `*-gate` hooks, and so on); the one added leaf is `commit`, authored by ANOTHER agent concurrently,
    and NEITHER `host probe` NOR `host capabilities` appears in it:
    ```
    $ ... | rg "^E       'host"      # (no output)
    ```
    Derived directly from the harness instead, which is the assertion those tests make:
    ```
    host probe        missing: set()  | covered: ['agent','help','json','no_color','non_tty','tty','usage_error']
    host capabilities missing: set()  | covered: ['agent','help','json','no_color','non_tty','tty','usage_error']
    declared_absent: ['prompts set']            # unchanged, still exactly the pinned drift
    host in undeclared: []
    ```
    So both new leaves carry a matching declaration AND full required-scenario coverage, and
    `declared_absent` is unchanged. `test_no_undeclared_parser_leaf_was_introduced` in the new module pins
    this narrowly (zero undeclared leaves whose name starts with `host`) so the guarantee survives even
    while the repo-wide gate is red for unrelated reasons.
    (8) FULL-SUITE FAILURE SETS ARE IDENTICAL BEFORE AND AFTER, both invocations run BARE:
    `python3 -m pytest` -> `32 failed, 4168 passed, 3 skipped, 4 xfailed` (baseline at the same HEAD:
    `32 failed, 4120 passed`; the +48 are the new module), and `python3 -m pytest -m ""` ->
    `38 failed, 4564 passed` (baseline `38 failed`). `diff` of the sorted FAILED lists before vs after is
    EMPTY for both, so no failure was introduced.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 6 E-leaves across 2 task groups, under the thresholds. One concern throughout: extend the existing capability contract so an action can be refused when its host cannot support it.

Open questions: OQ-01 and OQ-02 are resolved and need no maintainer decision. OQ-02 assigns ownership to the shipped module on repository evidence. OQ-01 is dissolved by deferring the runner wiring rather than answered, which is what lets this plan proceed without waiting on `rununify`. OQ-03 IS RESOLVED (2026-09-01, maintainer ruling; added at review as `- Finding: PR-002`, now closed `FIXED` in the typed review record). Two of the three capabilities this plan adds describe enforcement that does not exist in this repository, so there is nothing for their probes to attempt. The maintainer chose option (a): ship all three fields, with the two unenforced ones defaulting `False` and carrying a `probe_notes` entry that says so, because the threat model is ACCIDENT PREVENTION rather than adversarial defense and an honest declaration plus an accident-guard is worth shipping. E-02 is unblocked for `supports_fresh_verifier_session` and CONSTRAINED for the other two: declare, do not probe. No blocking question remains, so this plan now passes the pre-execution gate.

Scope fence: touch ONLY `agent_workflows/host_sandbox_profile.py`, `agent_workflows/cli.py`, `agent_workflows/command_surface.py`, the new test module, and `tests/test_host_sandbox_profile.py` for the SINGLE additive `CONTRACT_FIELDS` extension E-01 specifies (nothing else in that file; no existing assertion may be weakened, removed, or altered). Do NOT create a second capability module. Do NOT edit `host_capability_registry.py`. Do NOT touch `oc_runipd.py` or `agy_runipd.py` (deferred deliberately; touching them re-creates the `rununify` conflict this plan exists to avoid). Do NOT invent commit-interception or push-denial enforcement (OQ-03). Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or this orchestrator, and do NOT reimplement a rule another plan owns.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do NOT describe this plan as making runs safer: it lands the vocabulary and the checker, and nothing consults them until the follow-up wires the runners. Say so plainly in the terminal history.

Execution contract: commit ONLY the files changed, path-scoped, never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. Several sessions commit to this checkout concurrently.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
