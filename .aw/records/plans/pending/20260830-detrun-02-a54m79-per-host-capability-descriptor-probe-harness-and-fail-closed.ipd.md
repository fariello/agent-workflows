# IPD: Per-host capability descriptor, probe harness, and fail-closed action gating

- Date: 2026-08-30
- Kind: child
- Concern: TRUE AND STILL REAL (confirmed /plan-review 2026-08-30 pass 2). Unlike sibling `bmh754`, this plan's premise is NOT obsolete: the runners genuinely do assume uniform host capabilities, and `wtiso-07`'s review independently verified the default profile has NO filesystem write boundary. What is wrong is the OWNER, not the problem: approved `wtiso-07` (`1o4eif`) already builds the typed host capability contract and fail-closed dispatch, so this plan would create a second contract under different names for the same guarantees. Original text: Runners currently assume host assistants (OpenCode, Antigravity) provide uniform execution, sandboxing, and isolation capabilities, which can lead to silent failure, unconfined mutations, or unverifiable execution on degraded hosts.
- Scope: BLOCKED PENDING OQ-02/OQ-03 (corrected /plan-review 2026-08-30 pass 2). The capability VOCABULARY and the action-requirement map plus fail-closed preflight are genuinely unbuilt and should survive; the NEW MODULE (`host_capabilities.py`) and the NEW `aw host` CLI verb must not be built, and the runner wiring must wait for `rununify`. The surviving work belongs as an EXTENSION of the contract OQ-02 selects (most likely `wtiso-07`'s `host_sandbox_profile.HostSandboxCapabilities`). Original text: Implement the `HostCapabilityDescriptor` schema, on-disk descriptor cache, live and mock probe harnesses for `oc` and `agy` (worktree isolation, commit gateway, push denial, session separation, argv capture, timeout), action-level capability requirement mapping, and the fail-closed `RUN-HOST-CAPABILITY` preflight gate. Implements spec 25kzda Sections 5.2 and 4.2.
- Scope-Paths: agent_workflows/host_capabilities.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, tests/test_host_capabilities.py
- Item-Dependencies: executed:bmh754
- Status: approved
- Set: detrun
- Order: 2
- Highest E allocated: 07
- Author: antigravity
- Id: a54m79
- Approval: 2026-08-30, human ("approved"): Approved by the maintainer: 'I APPROVE all the reviewed IPDs' (2026-08-30 session, verbatim standing instruction before stepping away).
- Blocks-Release: next

## Workflow history
- 2026-08-30 approved (aw set, --by-human): Approved by the maintainer: 'I APPROVE all the reviewed IPDs' (2026-08-30 session, verbatim standing instruction before stepping away).
- 2026-08-30 /plan-review pass 2 (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN reaffirmed, but on CORRECTED reasoning; PR-201..PR-207. SELF-CORRECTION FIRST (PR-201): pass 1 claimed E-01..E-03 'largely duplicate' the shipped host_capability_registry.py. That was WRONG. Verified that module is a SKILL-DELIVERY conformance registry - its matrix is keyed on t1_policy/t2_layout/t3_global skill-import tiers and its 9 negative-probe classes are missing_skill, malformed_frontmatter, stale_adapter, path_precedence, server_auth, denied_permission, no_user_input, external_path_refusal, background_result_loss, none of which is a runner-safety guarantee. An INDEPENDENT prior review (wtiso-07) had already recorded the same conclusion, calling it 'a skill-probe registry, a different concern'; my pass-1 finding contradicted evidenced review and is retracted. So this plan is NOT mostly-shipped and must NOT be retired as redundant: its problem is real and unsolved. The surviving blocker is narrower and sharper - OWNERSHIP. Approved wtiso-07 builds HostSandboxCapabilities (7 fail-closed fields) in host_sandbox_profile.py; literal name overlap with this plan's 6 capabilities is ZERO (so no grep or aw check rule catches it) but three pairs are the SAME guarantee renamed (timeout_cancel~supports_process_tree_kill, argv_capture~emits_structured_tool_events, isolated_worktree+deny_push~supports_os_sandbox), while commit_gateway and fresh_verifier_session are genuinely new. NEW findings this pass: (PR-202) the 'hardened/mediated/observed' assurance levels recorded as a discovered convention appear NOWHERE in the codebase - the shipped vocabulary is unverified/supported/unsupported/degraded/failed/fail_closed_verified - and E-01's hardcoded .aw/state cache path is doomed because approved wtiso-05 relocates machine state out of the repo; (PR-206) BOTH required validations were unachievable, since tests/test_host_capabilities.py does not exist and `aw host` is not a verb at all (verified: aw rejects it), so an executor would have had to invent a public CLI surface to make a validation pass; (PR-207) OQ-01 was marked resolved 'from spec 5.2' but the spec names NO TTL and Section 6.2 explicitly defers 'the evidence TTL and probe recipes' to the repository, so the 24h figure was invented and silently contradicts the shipped 90-day default - reopened for the maintainer. Also imported wtiso-07's review-established hard rule that A PROBE MUST ATTEMPT, NOT INSPECT (measured fail-OPEN counterexample: every sysctl and both unshare/bwrap binaries indicated support while `unshare -Umr true` returned Operation not permitted), which this plan's E-02 did not forbid, plus its skip-is-not-a-pass honesty rule. All 7 E-items marked blocked with execution notes and all 7 V-items marked NOT TO BE COLLECTED; residue narrowed to 3 items with 5 prohibitions and a scope fence. Lint conforming at author and review-finalize. NO-GO pending maintainer answers to OQ-02 and OQ-03.
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): PR-006 fix. Normalized this history block to NEWEST-FIRST, the order `ipd_lifecycle._plan_status_events` assumes (it reverses to derive oldest-first). As authored the block was oldest-first, so the derived event stream read `to-review -> draft` and `aw check plans` reported `check.lifecycle-transition-invalid` ("backwards transition") on all 6 detrun plans. Verified pre-existing at pre-review commit `d4d265b6` (6 findings) and 0 after this fix. Content of every entry is unchanged; only line order.
- 2026-08-30 reviewed (aw set): plan-review: REJECT - NEEDS REPLAN (most of Set already shipped; collides with 3 approved Sets)
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001/PR-002. E-01..E-03 largely duplicate the shipped `host_capability_registry.py` (1593 lines, TTL expiry, unverified default, fail-closed migration, degraded/fail-closed-verified states, 9-class negative probes). The typed host capability contract is ALSO claimed by APPROVED `wtiso-07` (`1o4eif`), so two approved plans would own one contract (BLOCKING OQ-02). E-05 adds code to both runners, fighting APPROVED `rununify` (`5e4sb6`) (BLOCKING OQ-03). Genuine residue: the runner-safety capability vocabulary (greps to zero hits) and the action-to-capability map with fail-closed preflight, as an EXTENSION of the shipped registry. Gate closed. NO-GO.
- 2026-08-30 to-review (antigravity): deepened probe specifications, mock injection harness, degraded assurance states, and CLI introspection.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).
- 2026-08-30 draft (antigravity): created.

## Goal

**REPLAN - DO NOT EXECUTE. Verdict unchanged, but the pass-1 REASONING below was PARTLY WRONG and is
corrected here (/plan-review 2026-08-30 pass 2, PR-201).**

CORRECTION TO MY OWN PASS-1 FINDING (PR-001), stated plainly because a false "already shipped" claim is
as harmful as the false "net-new" claim that broke this Set in the first place. Pass 1 said E-01/E-02/E-03
"largely duplicate the shipped `host_capability_registry.py`". That OVERSTATED the overlap. Verified at
HEAD `c064ed4c`:

- The shipped `host_capability_registry.py` is a SKILL-DELIVERY conformance registry, a DIFFERENT
  concern. Its backing matrix (`.aw/system/workflows/conformance/tools/host_matrix.json`) is keyed on
  `t1_policy`/`t2_layout`/`t3_global` skill-import tiers, and its 9 negative-probe classes are
  `missing_skill`, `malformed_frontmatter`, `stale_adapter`, `path_precedence`, `server_auth`,
  `denied_permission`, `no_user_input`, `external_path_refusal`, `background_result_loss`. NONE of
  those is a runner-safety enforcement guarantee.
- An INDEPENDENT prior review reached this same conclusion and recorded it: the `wtiso-07` review states
  that `host_capability_registry.py` "is a skill-probe registry, a different concern" and credits that
  plan for "correctly declin[ing] to overload" it. My pass-1 finding contradicted an existing, evidenced
  review. That review is right and I was wrong.
- So the shipped registry supplies a reusable EVIDENCE MODEL (statuses incl. `unverified`/`degraded`/
  `fail_closed_verified`, TTL expiry, evidence digests, redaction, positive+negative probe pairing) that
  a replacement plan SHOULD study and may extend. It does NOT already answer this plan's question.

WHAT SURVIVES AS THE REAL BLOCKER (unchanged): the OWNERSHIP collision, which is narrower and sharper
than pass 1 described.

- `wtiso-07` (`1o4eif`, APPROVED) already builds "a typed host capability contract" as
  `HostSandboxCapabilities` in a new `agent_workflows/host_sandbox_profile.py`, with 7 fail-closed
  boolean fields, plus fail-closed dispatch via `select_execution_profile`.
- Literal field-name overlap with this plan's 6 capabilities is ZERO, but three are SEMANTIC
  DUPLICATES: `timeout_cancel` ~ `supports_process_tree_kill`; `argv_capture` ~
  `emits_structured_tool_events`; `isolated_worktree`/`deny_push` ~ `supports_os_sandbox`. Only
  `commit_gateway` and `fresh_verifier_session` have no counterpart.
- Two approved plans building two typed host-capability contracts, in two modules, with different names
  for the same guarantees, is the P8 violation. That is OQ-02, and it still needs a maintainer decision.
  Note the naming trap: because the names differ, `aw check` and a grep will NOT catch the duplication.
- `wtiso-07`'s review also establishes a HARD design constraint this plan violates: a capability probe
  MUST ATTEMPT, NOT INSPECT. That review measured a host where every sysctl and binary-presence signal
  said "sandbox available" while `unshare -Umr true` actually failed, so an inspection-based probe fails
  OPEN. This plan's E-02 says only "executes active and synthetic verification checks" and never forbids
  inspection-based probing.
- E-05 wires the preflight into BOTH `oc_runipd.py` and `agy_runipd.py`, fighting `rununify` (`5e4sb6`,
  approved), whose purpose is to collapse the ~93 percent duplication between those two files (OQ-03).

WHAT IS GENUINELY UNBUILT AND WORTH KEEPING: the runner-safety capability vocabulary
(`isolated_worktree`, `commit_gateway`, `deny_push`, `fresh_verifier_session`, `argv_capture`,
`timeout_cancel`) greps to ZERO hits in `agent_workflows/` (re-verified, all six); and the
action-to-capability requirement map (E-04) with its fail-closed `RUN-HOST-CAPABILITY` preflight is real,
needed work with no counterpart in either shipped module or `wtiso-07`. That residue should EXTEND
`wtiso-07`'s contract (or be merged into it) rather than open a third module, and only after OQ-02
assigns ownership.

Original goal, retained for the record: provide a rigorous per-host capability descriptor and probe
system that evaluates whether an agent host (`oc` or `agy`) can enforce required safety guarantees
before starting work, failing closed item-locally when required guarantees cannot be proven.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Capability descriptor data model and storage

- [ ] E-01 Create `agent_workflows/host_capabilities.py` defining `HostCapability`, `CapabilityAssurance`, `HostCapabilityEntry`, and `HostCapabilityDescriptor` with atomic serialization and cache persistence at `.aw/state/host_capabilities.json`.
  - Depends on: none
  - Expected outcome: **DO NOT BUILD AS WRITTEN (REPLAN). Not a duplicate of the shipped skill-probe registry (pass-1 correction PR-201), but it opens a THIRD capability module while approved `wtiso-07` already builds `HostSandboxCapabilities` in `host_sandbox_profile.py`. Two further defects: the cache path `.aw/state/host_capabilities.json` is hardcoded, and approved `wtiso-05` (`58ha43`) RELOCATES machine state out of the repo to an XDG dir keyed by checkout-id, so this path is doomed on arrival; and the 24h TTL conflicts with the shipped registry's 90d (`DEFAULT_EVIDENCE_TTL_DAYS`) with no rationale for diverging. Blocked on OQ-02.** Original expected outcome: Dataclasses serialize to/from JSON, compute cryptographic evidence digests, enforce TTL/staleness checks (default 24h), record positive/negative probe results, and support thread-safe cache reads/writes.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: blocked on OQ-02 (contract ownership vs approved wtiso-07) and OQ-03 (sequencing vs approved rununify). See the verdict in Expected outcome. Do not tick this box.

### Task group 2: Probe harness for OpenCode and Antigravity

- [ ] E-02 Implement probe runners in `agent_workflows/host_capabilities.py` for standard execution guarantees: `isolated_worktree`, `commit_gateway`, `deny_push`, `fresh_verifier_session`, `argv_capture`, and `timeout_cancel` for both OpenCode and Antigravity.
  - Depends on: E-01
  - Expected outcome: **DO NOT BUILD AS WRITTEN (REPLAN). The 6-capability vocabulary IS genuinely unbuilt (all six grep to zero hits) and is the valuable core of this plan. But it MUST NOT be a new parallel probe harness, and it MUST obey `wtiso-07`'s review-established rule: A PROBE MUST ATTEMPT, NOT INSPECT. That review measured a host where sysctls and both `unshare`/`bwrap` binaries indicated support while `unshare -Umr true` actually failed, so inspection-based probing fails OPEN - the exact silent degradation this plan exists to prevent. As written, 'active and synthetic verification checks' does not forbid inspection.** Original expected outcome: Probe suite executes active and synthetic verification checks against the local host installation, recording positive/negative results and evidence hashes in the descriptor.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: blocked on OQ-02 (contract ownership vs approved wtiso-07) and OQ-03 (sequencing vs approved rununify). See the verdict in Expected outcome. Do not tick this box.

- [ ] E-03 Implement a mock probe injection harness in `agent_workflows/host_capabilities.py` to allow testing degraded, unsupported, and expired host capability scenarios in unit and integration test suites without live binaries.
  - Depends on: E-02
  - Expected outcome: **KEEP THE IDEA, NOT THE MODULE. A mock/injection harness for degraded/unsupported/expired states is legitimate and necessary for deterministic fail-closed tests. It belongs beside whichever contract OQ-02 selects, and should reuse the shipped registry's status vocabulary (`unverified`/`degraded`/`fail_closed_verified`) rather than inventing a third set.** Original expected outcome: Test harnesses can inject synthetic capability states to verify fail-closed execution paths deterministically.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: blocked on OQ-02 (contract ownership vs approved wtiso-07) and OQ-03 (sequencing vs approved rununify). See the verdict in Expected outcome. Do not tick this box.

### Task group 3: Action requirements and fail-closed preflight

- [ ] E-04 Define the action capability requirement mapping table (`ACTION_REQUIRED_CAPABILITIES`) and implement `check_action_capabilities(host, version, mode, action)` in `agent_workflows/host_capabilities.py`.
  - Depends on: E-01, E-02
  - Expected outcome: **THE MOST VALUABLE ITEM; still blocked. The action-to-capability requirement map and `check_action_capabilities()` have NO counterpart in the shipped registry or in `wtiso-07`, and spec 5.2 requires them. Build this, against the OQ-02-selected contract, not against a new module.** Original expected outcome: Action types (read-only classification, review, authoring, execution, contract prompt, contractless prompt) declare exact required host guarantees and evaluate against the cached descriptor.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: blocked on OQ-02 (contract ownership vs approved wtiso-07) and OQ-03 (sequencing vs approved rununify). See the verdict in Expected outcome. Do not tick this box.

- [ ] E-05 Wire the `RUN-HOST-CAPABILITY` preflight check into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Depends on: E-04
  - Expected outcome: **DO NOT BUILD AS WRITTEN (REPLAN). Adds the preflight to BOTH runners, fighting approved `rununify` (`5e4sb6`). Sequence after `rununify` so it lands once in a unified runner (OQ-03).** Original expected outcome: Runner evaluates host descriptor before spawning executor session; unproven or stale capabilities fail item-locally with `host_capability_unavailable` without aborting independent items.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: blocked on OQ-02 (contract ownership vs approved wtiso-07) and OQ-03 (sequencing vs approved rununify). See the verdict in Expected outcome. Do not tick this box.

### Task group 4: CLI and probe management

- [ ] E-06 Add `aw host probe <host>` and `aw host capabilities [host]` commands to `agent_workflows/cli.py`.
  - Depends on: E-01, E-02
  - Expected outcome: **DO NOT BUILD AS WRITTEN (REPLAN). Verified `aw host` does NOT exist as a verb today, so this invents a new top-level command surface. That is a public-CLI decision requiring its own justification, and it collides with the pending `runnamecollapse` work on command-surface naming. Prefer extending an existing surface (e.g. `aw doctor`/`aw conf`) or defer entirely; the preflight (E-04) does not depend on it.** Original expected outcome: Users and automated runners can inspect host capability status, trigger on-demand re-probing, and view evidence digests in human table or JSON format.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: blocked on OQ-02 (contract ownership vs approved wtiso-07) and OQ-03 (sequencing vs approved rununify). See the verdict in Expected outcome. Do not tick this box.

### Task group 5: Test suite coverage

- [ ] E-07 Create `tests/test_host_capabilities.py` covering descriptor schema, cache TTL/staleness, mock and live probes, action requirement mapping, fail-closed preflight refusal, degraded capability handling, and CLI commands.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: **CANNOT BE WRITTEN YET. Its target module is undecided until OQ-02 resolves, and `100% branch coverage` is an unfalsifiable bar as stated (no coverage tool or threshold is named, and the repo does not gate on coverage). Restate as named test cases, and require attempt-vs-report agreement per `wtiso-07`'s PR-001.** Original expected outcome: Full pytest suite passes with 100% branch coverage on capability evaluation logic.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: blocked on OQ-02 (contract ownership vs approved wtiso-07) and OQ-03 (sequencing vs approved rununify). See the verdict in Expected outcome. Do not tick this box.

## Project conventions discovered (Step 0)

CORRECTED /plan-review 2026-08-30 pass 2 (PR-202). The Step 0 survey missed the two shipped modules and
the two approved plans that own this territory, which is why the plan proposed a third module.

- `.aw/state/` IS gitignored (verified: `.gitignore:60` matches `.aw/state/host_capabilities.json`). BUT
  approved `wtiso-05` (`58ha43`) relocates runtime machine-state OUT of the repo to an XDG state dir
  keyed by checkout-id, so hardcoding this cache path writes to a location that plan is actively
  removing. Consume the state-root helper; do not hardcode.
- Fail-closed principle: correct, and it is the plan's best instinct. Sharpened by `wtiso-07`'s review
  into an executable rule: A PROBE MUST ATTEMPT, NOT INSPECT, because inspection-based probing fails
  OPEN (measured counterexample recorded in that plan's E-02).
- Capability assurance levels `hardened`/`mediated`/`observed`: NOT a discovered convention. These appear
  nowhere in the codebase. The SHIPPED vocabulary is
  `unverified`/`supported`/`unsupported`/`degraded`/`failed`/`fail_closed_verified`
  (`host_capability_registry.ALL_CAPABILITY_STATUSES`). Inventing a third vocabulary would violate P8;
  reuse the shipped one.
- NOT DISCOVERED but decisive: `agent_workflows/host_capability_registry.py` (a skill-delivery probe
  registry, different concern, but a reusable evidence model) and approved `wtiso-07`'s
  `host_sandbox_profile.HostSandboxCapabilities` (the same typed-contract concern under different field
  names). Also `agent_workflows/host_adapters.py`.

## Findings

CORRECTED /plan-review 2026-08-30 pass 2 (PR-203). Both original findings are TRUE, and this plan's
underlying problem is real; the defect is that neither finding was checked against the two approved plans
already addressing it.

- TRUE: `oc_runipd.py` and `agy_runipd.py` assume worktree isolation and full subshell capture without
  verifying the host's actual runtime capabilities. Independently corroborated by `wtiso-07`'s review,
  which verified the default profile has NO filesystem write boundary (`start_new_session=True` exists
  only for `killpg` process-tree reaping).
- TRUE: host versions and run modes provide asymmetric primitives, and spec 5.2 requires a per-host
  descriptor for exactly this reason.
- MISSING FROM THE ORIGINAL SURVEY: approved `wtiso-07` already builds the typed contract and the
  fail-closed dispatch for this problem, and approved `rununify` is collapsing the two runner files this
  plan would edit. The finding is sound; the proposed OWNER is not.

## Proposed changes (ordered, validatable)

SUPERSEDED /plan-review 2026-08-30 pass 2 (PR-204). Do not perform this sequence: step 1 opens a third
capability module, step 5 fights approved `rununify`, and step 6 invents a top-level `aw host` verb that
does not exist. Steps 2 and 4 carry the real value.

The replacement shape, AFTER the maintainer answers OQ-02 and OQ-03:

1. Extend the OQ-02-selected contract (most likely `wtiso-07`'s `HostSandboxCapabilities` in
   `host_sandbox_profile.py`) with the runner-safety guarantees that have no counterpart, reconciling the
   three semantic duplicates rather than adding second names for them: keep one name per guarantee across
   `timeout_cancel`/`supports_process_tree_kill`, `argv_capture`/`emits_structured_tool_events`, and
   `isolated_worktree`+`deny_push`/`supports_os_sandbox`; add `commit_gateway` and
   `fresh_verifier_session`, which are genuinely new.
2. Every probe MUST ATTEMPT, NOT INSPECT, and any nonzero exit, exception, or timeout is `False`.
3. Add the action-to-capability requirement map plus `check_action_capabilities()` and the fail-closed
   `RUN-HOST-CAPABILITY` refusal (the plan's most valuable, wholly-unbuilt contribution).
4. Reuse the shipped status vocabulary and evidence model from `host_capability_registry.py`; do not
   invent `hardened`/`mediated`/`observed`.
5. Resolve the evidence TTL explicitly (spec 6.2 leaves it to the repository; see OQ-01) and read the
   cache path from the state-root helper, not a hardcoded `.aw/state/...`.
6. Sequence the runner wiring after `rununify` so it lands once.

Original sequence, retained for the record:

1. ~~Implement `HostCapabilityDescriptor` and cache storage in `host_capabilities.py` (E-01).~~
2. Implement probe harnesses for `oc` and `agy` (E-02) - keep, but attempt-not-inspect and no new module.
3. Implement mock probe injection harness for testing (E-03) - keep the idea.
4. Implement action requirement mapping and preflight check (E-04) - KEEP; this is the core value.
5. ~~Integrate preflight into runner dispatch loops (E-05).~~ Defer behind `rununify`.
6. ~~Add CLI inspection/probing commands (E-06).~~
7. ~~Cover with comprehensive tests in `test_host_capabilities.py` (E-07).~~ Retarget once OQ-02 resolves.

## Deferred / out of scope (with reason)

- **Kernel-level eBPF sandboxing**: Hardware/kernel sandboxing is an OS-level concern; host capability probes verify tool policy denial and credential withholding at the agent execution boundary.
- **DAG queue cascade logic**: Propagating `host_capability_unavailable` skips down the dependency graph is implemented in child plan `detrun-03` (`kaygwo`).

## Scope check

CORRECTED /plan-review 2026-08-30 pass 2 (PR-205). Unlike sibling `bmh754`, this plan is NOT mostly
duplicated code; its problem is OWNERSHIP and COLLISION.

- Over-scope: the new module (E-01) and the new `aw host` CLI surface (E-06). Both add territory the repo
  already covers or has not agreed to: a third capability module against approved `wtiso-07`'s contract,
  and a brand-new top-level verb (`aw host` verified absent) introduced as a side effect of a runner
  feature rather than a considered public-CLI change.
- Under-scope: three things the plan needed and lacked. (1) No reconciliation with the two approved plans
  that own this territory (`wtiso-07`, `rununify`), so its child boundary is unsafe. (2) No
  attempt-not-inspect requirement on the probes, the one rule that separates a fail-closed gate from a
  fail-OPEN one. (3) No decision on the evidence TTL, which spec 6.2 explicitly delegates to the
  repository and which OQ-01 answered with a number that silently contradicts the shipped 90-day default.
- Original text, retained for the record: "Over-scope: none. Strictly implements host capability detection
  and action-level gating. Under-scope: none. Covers both OpenCode and Antigravity hosts across all action
  types and capability dimensions."

## Required tests / validation

CORRECTED /plan-review 2026-08-30 pass 2 (PR-206). Both original items were unachievable as written.

- ~~`python3 -m pytest tests/test_host_capabilities.py`~~ - the module does not exist and its correct
  location is undecided until OQ-02 resolves.
- ~~`aw host capabilities oc` / `aw host capabilities agy` returning a structured table~~ - NOT
  achievable: `aw host` is not a verb (verified; `aw` rejects it as an invalid choice). An executor
  following this literally would have to invent a public CLI surface to make a validation pass.
- The honest bar for the replacement: the full suite at no-worsening against a freshly measured baseline
  (do NOT claim `aw check plans` passes; it is RED on 222 pre-existing findings owned by other Sets),
  plus per-capability ATTEMPT-VS-REPORT AGREEMENT evidence, plus a test proving a refused capability
  fails ONLY its own item while independent items continue.
- Honesty requirement inherited from `wtiso-07`'s review: a SKIPPED probe test is NOT a pass. If a
  guarantee cannot be exercised on the running host, record it UNVERIFIED with the probe output; never
  let `1 skipped` stand in for `1 passed`.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Section 5.2.
- Updates runner documentation to describe capability probing, cache TTLs, and troubleshooting missing guarantees.

## Open questions

### OQ-01: What is the default TTL for cached probe evidence?

- Blocking: no
- Status: open
- Owner: maintainer (was wrongly marked resolved)
- Resolution or deferral rationale: REOPENED /plan-review 2026-08-30 pass 2 (PR-207). This was marked
  `resolved` and attributed to "spec 25kzda Section 5.2", but the spec does NOT specify a number. Section
  6.2 explicitly lists "the evidence TTL and probe recipes for each host capability descriptor entry"
  among the "implementation choices still requiring repository-level definition". So the 24-hour figure
  was invented, not derived, and it silently CONTRADICTS the shipped
  `host_capability_registry.DEFAULT_EVIDENCE_TTL_DAYS = 90`. Two different TTLs for host-capability
  evidence in one repo needs a deliberate decision, not a number chosen in passing. The invalidation
  TRIGGERS the original answer named (host binary hash, version string, or config change) ARE well-grounded
  in spec 5.2 and limit 9 and should be kept regardless of the number. Recommendation: adopt a short TTL
  for enforcement-critical runner guarantees (they are cheap to re-probe and expensive to get wrong) while
  keeping the shipped 90-day default for skill-delivery evidence, and record the divergence explicitly so
  it does not read as drift.

### OQ-02: Which module owns the typed host capability contract?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN, and the decisive blocker for this plan. Approved `wtiso-07`
  (`1o4eif`) builds `HostSandboxCapabilities` (7 fail-closed fields) in a new `host_sandbox_profile.py`;
  this plan builds `HostCapabilityDescriptor` (6 capabilities) in a new `host_capabilities.py`. Literal
  name overlap is ZERO, so no grep or `aw check` rule will catch it, but three pairs are the SAME
  guarantee under different names. A third module (`host_capability_registry.py`) already exists for the
  unrelated skill-delivery concern. Pick ONE owner for the runner-safety contract and make the other a
  consumer. Recommendation: `wtiso-07`'s module, since it is approved, already fail-closed by construction,
  and already carries the attempt-not-inspect discipline; this plan's residue then becomes an extension
  (adding `commit_gateway`, `fresh_verifier_session`, and the action-requirement map).

### OQ-03: Must the runner wiring wait for `rununify`?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN. E-05 edits both `oc_runipd.py` and `agy_runipd.py`, while
  approved `rununify` (`5e4sb6`) exists to collapse their ~93 percent duplication. Landing E-05 first
  doubles the merge surface `rununify` must reconcile. Recommendation: sequence after `rununify` so the
  preflight lands once in the unified runner; accept the resulting delay to this plan's release gate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is blocked on OQ-02/OQ-03; collecting this would mean proving a third parallel capability module was built.** Original required evidence: Python test showing `HostCapabilityDescriptor` serializing, deserializing, and enforcing TTL expiry.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is blocked on OQ-02/OQ-03; collecting this would mean proving a third parallel capability module was built.** Original required evidence: Test execution showing probes running against mock/real host binaries and returning structured capability records.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is blocked on OQ-02/OQ-03; collecting this would mean proving a third parallel capability module was built.** Original required evidence: Test verifying mock probe injection allowing synthetic degraded or missing capabilities in test environments.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is blocked on OQ-02/OQ-03; collecting this would mean proving a third parallel capability module was built.** Original required evidence: Truth table test verifying action requirement matching across all action types and capability combinations.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is blocked on OQ-02/OQ-03; collecting this would mean proving a third parallel capability module was built.** Original required evidence: Test running runner with missing capability fixture, verifying item fails with `RUN-HOST-CAPABILITY` and independent items continue.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is blocked on OQ-02/OQ-03; collecting this would mean proving a third parallel capability module was built.** Original required evidence: CLI session showing `aw host capabilities` and `aw host probe` formatting human-readable and JSON output.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is blocked on OQ-02/OQ-03; collecting this would mean proving a third parallel capability module was built.** Original required evidence: `pytest tests/test_host_capabilities.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**GATE: CLOSED. `REJECT - NEEDS REPLAN` (/plan-review 2026-08-30, reaffirmed pass 2 on corrected
reasoning).** Do NOT execute and do NOT approve. Every E-item is `Execution state: blocked` with an
execution note, and every V-item's evidence is NOT TO BE COLLECTED, so nothing here can be ticked. An
executor reaching this gate must STOP and report.

IMPORTANT DISTINCTION FROM SIBLING `bmh754`: this plan is NOT mostly-already-shipped. Pass 1 said its
first three items duplicated `host_capability_registry.py`; that was WRONG and is corrected in `## Goal`
(that module is a skill-delivery probe registry, a different concern, as an independent `wtiso-07` review
also concluded). This plan addresses a REAL, unsolved problem. It is blocked on OWNERSHIP and SEQUENCING,
not on redundancy. Do not retire it as "already done"; that would lose genuinely needed design.

Open questions: THREE open, all blocking-or-material, and OQ-02/OQ-03 need YOU:
- OQ-02 (blocking): which module owns the typed host capability contract - `wtiso-07`'s
  `host_sandbox_profile.py` or a new one here. Recommendation: `wtiso-07`'s.
- OQ-03 (blocking): whether the runner wiring waits for `rununify`. Recommendation: yes.
- OQ-01 (material, reopened): the evidence TTL, which spec 6.2 delegates to the repository and which was
  previously "resolved" with an invented 24h that contradicts the shipped 90-day default.

Retirement: retire with the parent Set `detrun` (`r4mbcw`) ONLY once its surviving design is carried
forward. Prepend a `RETIRED 2026-08-30: <reason>; superseded by <path/commit>` header and `git mv` to
`.aw/records/plans/superseded/`. Do NOT file under `executed/`; nothing was implemented.

Release gate: carries `- Blocks-Release: next`. The residue below MUST be re-gated onto its successor (or
the gate explicitly cleared), because unlike `bmh754` this residue is substantial.

SURVIVING RESIDUE, for the replacement (after OQ-02/OQ-03 are answered):

1. The 6 runner-safety capabilities (all verified absent: `isolated_worktree`, `commit_gateway`,
   `deny_push`, `fresh_verifier_session`, `argv_capture`, `timeout_cancel`), added to the OQ-02-selected
   contract, reconciling the 3 semantic duplicates to ONE name per guarantee.
2. The action-to-capability requirement map plus `check_action_capabilities()` and the fail-closed
   `RUN-HOST-CAPABILITY` refusal. This is the plan's most valuable contribution and has no counterpart
   anywhere.
3. A mock/injection harness for degraded/unsupported/expired states, reusing the SHIPPED status vocabulary.

Explicit prohibitions for that replacement: do NOT create `agent_workflows/host_capabilities.py`; do NOT
add an `aw host` top-level verb (it does not exist, and inventing a public CLI surface is a separate
decision); do NOT invent the `hardened`/`mediated`/`observed` assurance vocabulary (the shipped one is
`unverified`/`supported`/`unsupported`/`degraded`/`failed`/`fail_closed_verified`); do NOT hardcode
`.aw/state/host_capabilities.json` (approved `wtiso-05` relocates machine state out of the repo - use the
state-root helper); and do NOT write an INSPECTION-based probe.

THE PROBE MUST ATTEMPT, NOT INSPECT (inherited hard rule, from `wtiso-07`'s review): deciding a capability
from sysctls, `sys.platform`, or binary presence fails OPEN. That review measured a host where
`unprivileged_userns_clone=1` and both `unshare` and `bwrap` were installed, yet `unshare -Umr true`
returned `Operation not permitted`. Execute a minimal real attempt in a subprocess; treat ANY nonzero
exit, exception, or timeout as `False`.

Scope fence for that replacement: the OQ-02-selected capability module, plus its test module. Do NOT edit
`oc_runipd.py`/`agy_runipd.py` until `rununify` lands (OQ-03). Both runners and `cli.py` are actively
contended in this SHARED CHECKOUT: verify `git diff --cached --name-only` before every commit and unstage
anything not yours. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do
NOT claim `aw check plans` passes (RED on 222 pre-existing findings from other Sets); the bar is
no-worsening against a fresh baseline. A SKIPPED probe test is NOT a pass: if a guarantee cannot be
exercised on the running host, record it UNVERIFIED with the probe output rather than letting `1 skipped`
stand in for `1 passed`.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never
`git add -A`, never push. Post-gate lifecycle is `aw ipd finalize`, never a hand-move. Do not create or
push a tag or release.
