# IPD: Probe host-granular egress filtering by attempt, two-sided and hermetic

- Date: 2026-10-01
- Kind: child
- Concern: Spec `25kzda` 5.2 requires the host descriptor to answer, from probe evidence, whether the host can deny push-capable network routes. Nothing answers it. `supports_deny_push` was removed by plan `01reg8` precisely because it was declared and never probed, and the Landlock route measured in research `uq4y6q` cannot answer it at all because its rules are port-only. The prerequisite for any honest answer is a capability decided by an EXECUTED attempt at the only mechanism that can express a destination partition.
- Scope: Add ONE capability, `supports_egress_filtering`, decided by an executed two-sided hermetic probe that creates a network namespace, proves egress is denied by default, and proves a parent-held control channel remains reachable. The probe needs no external network. The capability gates NO action, adds NO finding code, and is NOT named for push denial.
- Scope-Paths: agent_workflows/host_sandbox_profile.py, tests/test_host_sandbox_profile.py, tests/test_host_capability_extension.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- From-Backlog: sv9ce4
- From-Spec: 25kzda
- Work-Kind: feature
- Priority: low
- Set: netnsfilter
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: nxh5s4

## Workflow history
- 2026-10-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: nxh5s4 verified (set netnsfilter, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261009-4dktme-01-4dktme-test-collision-guard-bites-by-mutation-fails-becau.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run); out-of-scope .aw/records/backlog/open/20261009-6dmayw-01-6dmayw-runner-safety-probe-execution-uncached-in-test-sui.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run)]
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): REVIEWED - OPEN QUESTIONS; PR-101..PR-104 FIXED (round 2); OQ-03 non-blocking, open
- 2026-10-07 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-101 (MEDIUM, fixed: F-5/OQ-02 per-item probe cost is stale, runners now freeze the descriptor per run via ensure_frozen_host_capabilities; resumed-run default False recorded), PR-102 (LOW, fixed: V-03 bar is an empty after-minus-before failing set, plus a suite wall-time measurement), PR-103 (LOW, fixed: pi3bk8 status is live, re-derive), PR-104 (LOW, fixed: backlog close ownership). Probe design re-demonstrated at HEAD e9de18a08 (True/not-enforced/launcher-missing distinct). OQ-03 (naming, non-blocking, maintainer, carried by wcbpqf) still open. Lint clean at author and review-finalize. Record: `.aw/records/reviews/20261001-netnsfilter-01-nxh5s4-probe-host-granular-egress-filtering-by-attempt-two-sided-an.review.md` Round 2.
- 2026-10-07 to-review (aw set): returned to review: Set-level validation sweep owned by wn956n E-05/V-05; coverage pass recorded; open questions are non-blocking
- 2026-10-06 draft (aw set): demoted approved -> draft: APPROVAL WITHDRAWN: returned to authoring by gradcover 52opph: uncovered obligation: Bare pytest run green with actual summary line pasted
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-03 reviewed (aw set): plan-review revisions applied; see review record

- 2026-10-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008 all fixed; OQ-03 (naming, non-blocking, maintainer, carried by `wcbpqf`) left open (review record 20261001-netnsfilter-01-nxh5s4-...review.md).
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `sv9ce4`. The probe shape specified here was BUILT AND RUN during authoring (research `akmzyq` Finding 7), five timed runs, rather than designed on paper, because the sibling Set's measured lesson was that a plausible probe design can be impossible.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give spec `25kzda` 5.2's network requirement its first probed answer that is capable of being a real
boundary: a capability that is True only when THIS host actually created a network namespace in which
egress was denied while a parent-held control channel stayed reachable, and False with an explanatory
note on every other host.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the probe

- [x] E-01 Add `_probe_egress_filtering` to `agent_workflows/host_sandbox_profile.py`, a two-sided executed probe modeled on `_probe_landlock` and held to the same standard the module docstring states as "EVERY RUNG MUST PROVE A DENIAL, NOT A LAUNCH". THE PARENT OWNS BOTH ENDPOINTS. The parent binds a loopback TCP listener (standing in for a denied remote) and an AF_UNIX socket (standing in for the allowed control channel), then launches a child via `unshare -Urn --map-root-user` that must (a) FAIL to reach the TCP listener and (b) SUCCEED in reaching the AF_UNIX socket. Distinguish the outcomes by exit code exactly as `_denial_checker_source` does: success, jail-too-tight (the allowed side failed), and not-enforced (the denied side was reached). Route the subprocess through `_run_probe` so any nonzero exit, exception or timeout maps to False, and honor `_PROBE_TIMEOUT_SECONDS`. The probe must apply the `CERTIFIED_PLATFORM` check ITSELF and return False with a note on any other platform, because `detect_host_capabilities` runs `probe_runner_safety_capabilities` BEFORE its own `if not plat.startswith(CERTIFIED_PLATFORM)` gate (it is guarded only by `plat == running_platform`), so on a darwin interpreter the probe IS called.
  - MECHANISM SEAM (added at review, required by E-04 and E-05). Hold the namespace launcher as a module-level tuple, for example `_EGRESS_PROBE_NS_ARGV = ("unshare", "-Urn")` (`-r` already IS `--map-root-user`; passing both is redundant but harmless), and build the child argv from it. Tests then arrange MECHANISM outcomes by swapping that tuple rather than patching the probe's return value: `("unshare", "-Ur")` creates a user namespace WITHOUT a network namespace, so the denied side is reachable; a nonexistent binary makes namespace creation fail. Both were demonstrated at review (F-9).
  - THE ALLOWED SIDE MUST BE A FILESYSTEM-PATH AF_UNIX SOCKET, never an abstract one (`"\0name"`): the abstract socket namespace is per network namespace, so an abstract socket does NOT cross (F-9, `ConnectionRefusedError: [Errno 111]`). Keep the socket path short (a `tempfile.TemporaryDirectory` with a short prefix) because `sun_path` is limited to about 108 bytes.
  - THE PARENT MUST OBSERVE THE ALLOWED SIDE, not only trust the child's exit code: True requires child rc 0 AND the parent having `accept`ed a connection on its AF_UNIX socket and received the child's token. A listening socket with a backlog lets the child's `connect` complete before the parent calls `accept`, so a blocking `_run_probe` followed by a short-timeout `accept` works with no thread (F-9).
  - WHY BOTH SIDES AND WHY AF_UNIX IS THE ALLOWED SIDE. A one-sided probe asserting only "egress was denied" would return True for a namespace so isolated that no control channel can reach the parent, which is useless as a boundary because the confined agent could not reach the model API either. Measured during authoring (research `akmzyq` Finding 2): an AF_UNIX socket DOES cross the namespace boundary (`unix socket across netns: PARENT-PROXY-REACHED`) while direct egress from the same child was refused (`OSError [Errno 101] Network is unreachable`) in ONE run. That pair is exactly the two-sided property, and it is why the allowed side needs no veth, no NAT, no bridge and no `slirp4netns`.
  - Depends on: none
  - Expected outcome: A probe returning `(bool, note)`, True only on proven two-sided behavior, False with an explanatory note on every other outcome including a host that cannot create a namespace and any non-Linux platform. On a host where `unshare -Urn --map-root-user true` succeeds, the probe MUST return True; a design that cannot return True on such a host has not met this item.
  - Execution state: performed

- [x] E-02 Make the probe HERMETIC and give its note the evidence. It must require no external network and no DNS, so it is runnable in CI and on an offline host: both endpoints are parent-held and loopback or AF_UNIX only. The note must state what was attempted and what the kernel did, naming the namespace mechanism used and the observed refusal, so a reader of `aw host capabilities` sees evidence rather than a bare verdict. The note must ALSO state the two limits this probe does not cover: that it proves a namespace can be created and partitioned, NOT that any particular destination policy is enforced (that is child 02's), and that it proves nothing about whether a confined process could remove the boundary (child 03's).
  - Depends on: E-01
  - Expected outcome: A probe whose note is usable as evidence and which cannot be read as claiming a complete push boundary. Measured during authoring, the probe shape costs a mean well under 0.1s (five runs: 0.079s, 0.090s, 0.040s, 0.040s, 0.036s), so hermetic does not mean slow; re-derive the figure on the executing host rather than copying it.
  - Execution state: performed

### Task group 2: the contract surface

- [x] E-03 Add `supports_egress_filtering` to `HostSandboxCapabilities` defaulting False, add the `CAP_EGRESS_FILTERING` constant, register it in `RUNNER_SAFETY_CAPABILITIES`, wire `_RUNNER_SAFETY_PROBES[CAP_EGRESS_FILTERING] = _probe_egress_filtering` (a real probe, NOT the `None` sentinel that marks declared-not-probed), export the constant in `__all__`, and confirm the verdict and its `probe_notes` entry reach `detect_host_capabilities` (they do with no edit there: it already applies every verdict and note `probe_runner_safety_capabilities` returns, via `setattr(caps, name, supported)` and `caps.probe_notes.update(notes)`). Do NOT add it to `ACTION_CAPABILITY_REQUIREMENTS` and do NOT add an action class: `ACTION_CLASSES` stays `(ACTION_READ_ONLY,)`. IN THE SAME PASS append `"supports_egress_filtering"` to `tests/test_host_sandbox_profile.py`'s `CONTRACT_FIELDS` tuple, because omitting it leaves the suite RED at the end of this item: `test_new_contract_fields_and_defaults` iterates `RUNNER_SAFETY_CAPABILITIES` and asserts every member appears in `CONTRACT_FIELDS`, which it imports from the other test module.
  - Depends on: E-02
  - Expected outcome: `aw host capabilities` reports the new row with its note automatically, because `host_cmd._capability_rows` introspects `caps.to_dict()` for bool values rather than reading a name list. No action is gated, so no run behavior changes. The suite is GREEN at the end of this item, not merely at the end of the plan.
  - Execution state: performed

### Task group 3: tests that can say no

- [x] E-04 Pin the probe's fail-closed behavior in `tests/test_host_sandbox_profile.py`: a test driving `_probe_egress_filtering` DIRECTLY and asserting the returned `(bool, note)` pair so the probe is exercised rather than only its registration; a test asserting a RAISING probe yields False with the note recording the exception, mirroring `test_a_raising_probe_yields_not_supported` in `tests/test_host_capability_extension.py` (which patches `_RUNNER_SAFETY_PROBES`, the path a runner-safety capability actually takes) and NOT `test_a_raising_probe_is_treated_as_unavailable` in this file (which patches `_SANDBOX_LADDER`, a mechanism this capability is deliberately not registered in); and a test asserting the probe reports False rather than raising when the namespace cannot be created, arranged by swapping `_EGRESS_PROBE_NS_ARGV` to a nonexistent binary (restored in `finally`); plus a test asserting a NOT-ENFORCED arrangement (`("unshare", "-Ur")`, no network namespace) yields False with a note saying the denied side was reached. The direct-probe test's EXPECTED value is decided by EXECUTING `unshare -Urn true` in the test (an attempt, not a `shutil.which` presence check): True when that succeeds, False otherwise, so the test is honest on a host or CI runner whose user namespaces are restricted and still fails a constant-returning probe on a capable one.
  - DO NOT ASSERT "the verdict equals a re-run of the probe", which is VACUOUS: `probe_runner_safety_capabilities` is uncached, so such an assertion reduces to `probe() == probe()` and passes for a probe returning a constant, which is the fail-open shape this area's test discipline exists to reject. Assert against an ARRANGED outcome or against the note naming its evidence.
  - Depends on: E-03
  - Expected outcome: The new field carries the same default-False and snapshot coverage every other contract field has, and the probe's fail-closed behavior is pinned by tests that would FAIL against a constant-returning probe.
  - Execution state: performed

- [x] E-05 Add the capability's row to `tests/test_host_capability_extension.py`'s `PRESENCE_VS_OBSERVATION` table, whose own comment demands "ONE CLAIM, ONE ROW PER PROBE: no runner-safety capability may be decided by a HELPER EXISTING". The row's `arrange` must make the mechanism PRESENT AND REACHABLE while the partition is NOT observed, which is the fail-open shape the table exists to catch: arrange it so the namespace is created but the denied side is reachable, and restore in a `finally` because the patch is process-global. Do NOT arrange it by patching the probe to return False, which tests the patch rather than the mechanism. Use the E-01 seam: swap `_EGRESS_PROBE_NS_ARGV` to `("unshare", "-Ur")`, which really creates a namespace and really partitions nothing (F-9: `rc 4 | denied REACHED - not enforced`). The row's presence witness must be what a naive probe WOULD inspect, here the `unshare` executable; if the table's witness column is `(module, attribute)`-shaped, the consumer must accept this row's witness as an executable checked with `shutil.which`, or the row records `("shutil", "which")` and the consumer asserts `shutil.which("unshare")` is not None.
  - ADD THE POSITIVE ROW TOO (added at review). The table's own fresh-verifier rows pair each negative row with a positive one because "without it every negative row above is satisfied by a prober that answers `False` unconditionally". Add an `_unarranged` row for this capability whose expected verdict is True on a host where `unshare -Urn true` succeeds. Because the table's expected column is a literal, the consumer must compute this row's expectation from that executed check (or the row is skipped with an explicit reason on an incapable host, which per the stated policy leaves the positive half UNVERIFIED there, and V-05 must say so).
  - COORDINATE WITH `pi3bk8`. Its E-06 writes the same consumer; it declares `executed:x2dwu5` (which HAS executed). Its status is a LIVE fact (it read `approved` at authoring and `to-review` at the 2026-10-07 review), so re-derive it with `aw find plans pi3bk8` at execution rather than trusting either. If it has executed, reuse its consumer and add rows only. If not, write a consumer here that `pi3bk8` can reuse, and record in this plan's evidence that `pi3bk8` E-06 will find a live consumer already present.
  - VERIFY THE TABLE HAS A LIVE CONSUMER BEFORE ADDING A ROW, and if it does not, this item's first job is to write one. Measured during authoring: an `ast` walk of that file for references to `PRESENCE_VS_OBSERVATION` returned exactly one hit, its own assignment, because commit `80db6750` deleted its only consumer. The sibling Set's plan `pi3bk8` E-06 is scheduled to restore that consumer; if `pi3bk8` has not executed when this plan runs, a row added here asserts NOTHING. So check first, and write the consumer if absent. Restore no part of the deleted test that read production source text or counted symbols, which is why it was deleted (AGENTS.md P16).
  - Depends on: E-03
  - Expected outcome: A present-but-unpartitioned mechanism yields False, pinned by a row that a live test actually reads, provable by inverting the probe and seeing the test fail.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A capability may be set True ONLY by code that executed a probe for it: `HostSandboxCapabilities`'
  docstring states "Every capability defaults to False: an UNPROBED host claims NOTHING
  (fail-closed)."
- Presence inference is FORBIDDEN IN WRITING, in `host_sandbox_profile`'s module docstring (the
  `supports_commit_gateway` bullet: "Inferring support from the presence of the driver-side
  `git_commit_helper.offer_commit` helper is FORBIDDEN") and again in the `_DECLARED_UNENFORCED`
  rationale. This bites directly here: `unshare`, `bwrap` and `slirp4netns` were ALL installed on the
  host of research `uq4y6q` and namespace creation still failed, so a presence check would report
  True on a host that cannot enforce anything.
- A probe passes only by proving a DENIAL, never a launch: the module docstring states "EVERY RUNG
  MUST PROVE A DENIAL, NOT A LAUNCH", because a misconfigured permissive jail "starts perfectly
  cleanly and enforces nothing". `_denial_checker_source` encodes it with distinct exit codes.
- Probe failures are swallowed to False at three layers: `_run_probe` maps any `OSError` or
  `SubprocessError` including `TimeoutExpired` to nonzero, `_probe_linux_sandbox` catches any
  exception, and a non-Linux platform short-circuits. A new probe joins that discipline, never raises.
- Runner-safety verdicts are deliberately NOT cached, unlike the sandbox ladder, because
  "a stale memo here would be a way for one turn's verdict to outlive the state it was measured
  against". Membership in `_RUNNER_SAFETY_PROBES` also grants the `forced_runner_safety_verdicts`
  test seam for free.
- `aw host capabilities` needs no change to show a new field: `host_cmd._capability_rows` introspects
  `caps.to_dict()` for bool values so "a field added to the contract cannot silently vanish from the
  report", and it renders each verdict's `probe_notes` entry directly beneath it as a `why:` line.
- A test must exercise behavior, never pin code structure (AGENTS.md P16): no `inspect`, `ast` or
  regex reads of production source.
- Cite code by SYMBOL or quoted content string, never by a bare line number (`IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | A namespace denies ALL egress by default, so denial is the default and each allowance is explicit | Research `akmzyq` Finding 1: an in-namespace connect returned `OSError [Errno 101] Network is unreachable`; `bwrap --unshare-net` reached the same state | The probe's denied side needs no rule to be installed, which is why it is hermetic and cheap. This is the opposite posture from the Landlock port rules, where everything unnamed stays reachable. |
| F-2 | AF_UNIX crosses the namespace boundary, so the allowed side needs no networking | Research `akmzyq` Finding 2: `unix socket across netns: PARENT-PROXY-REACHED` with `parent received: b'HELLO-FROM-NETNS'`, in the same run where direct egress was refused | Decides the probe's design: both endpoints are parent-held, no veth, no NAT, no `slirp4netns`. It also decides what the capability MEANS, namely that a control channel can survive the partition. |
| F-3 | The probe shape was BUILT AND RUN, not designed on paper | Research `akmzyq` Finding 7: three consecutive runs reported `denied_side: refused ... allowed_side: BROKER-REACHED` with `probe rc: 0`, and the three failure shapes are distinguished by exit code | E-01's design is demonstrated rather than proposed. The sibling Set's plan `pi3bk8` F-10 records the alternative outcome: a plausible probe design that could NEVER return True, discovered only by building it. |
| F-4 | Namespace availability VARIES BY HOST, so the probe must be the authority | Research `akmzyq` Finding 0: `unshare -Urn --map-root-user true` returns rc 0 here, while research `uq4y6q` recorded the same command failing with `write failed /proc/self/uid_map: Operation not permitted` on its host | The capability is genuinely per-host, which is the whole reason it must be probed. Neither measurement is wrong; the older host was itself inside a namespace denying nested mapping. |
| F-5 | The cost is small but NOT zero, and the group chosen is uncached | Five timed authoring runs: 0.079s, 0.090s, 0.040s, 0.040s, 0.036s, against a warm `detect_host_capabilities('opencode')` measured at 0.052s on the same host | Registering in `RUNNER_SAFETY_CAPABILITIES` means paying a subprocess per call, roughly doubling that call. CORRECTED AT REVIEW: it IS paid per queue item, because `oc_runipd._apply_execution_profile` calls `detect_host_capabilities("opencode")` unconditionally on every opencode dispatch, before checking the requested profile (the `runner_shared.execute_item_core` preflight call is the one that fires for nothing today). Still acceptable: the review re-measured the probe shape at 0.045s on this host, against an agent turn measured in minutes. Recorded as a measured choice; OQ-02 holds the reasoning. RE-CORRECTED AT THE 2026-10-07 REVIEW: the per-item claim is now STALE. `oc_runipd._apply_execution_profile` no longer calls `detect_host_capabilities` directly; it calls `runner_shared.ensure_frozen_host_capabilities`, which returns the run-scoped descriptor frozen in `state["host_capabilities"]` and probes only when that key is absent (bqtgmo). So a runner pays the probe ONCE PER RUN (at run initialization, where `runner_shared` calls `detect_host_capabilities(cli_host)`), plus once per `aw host capabilities` call. A resumed run whose frozen descriptor predates this field rehydrates through `HostSandboxCapabilities.from_dict`, which keeps only known fields, so the new field reads its default False for that run: fail-closed, and correct because no action is gated. The 2026-10-07 re-measurement through `_run_probe` was about 0.19s per call on a loaded host, so the authoring figure is not a bound; re-derive it. |
| F-6 | A live negative test pins `supports_deny_push`'s absence | `tests/test_host_capability_extension.py` class `DenyPushRemovedTests` asserts the field, `CAP_DENY_PUSH`, the action classes and the `deny_push` output string are all absent | This plan's capability has a DIFFERENT name for a substantive reason, not to evade the guard: it proves a namespace partition, not push denial. The guard must still pass untouched after this plan. |
| F-7 | `PRESENCE_VS_OBSERVATION` may still be DEAD DATA when this plan runs | Measured during authoring: an `ast` walk for references returns exactly one, its own assignment; commit `80db6750` deleted the only consumer. Sibling plan `pi3bk8` E-06 is scheduled to restore it but is a different Set with its own schedule | E-05 must CHECK for a live consumer and write one if absent, rather than adding a row and pasting a green line that proves nothing. This is why E-05 carries the check as its first job. |
| F-8 | The action preflight is wired but fires for nothing today | `runner_shared.execute_item_core` calls `preflight_host_capabilities`, but `RUNNER_ACTION_TO_CONTRACT_ACTION` is empty and `runner_action_contract_class` returns None for every action; the module docstring's HONEST LIMIT says "today this prevents nothing on its own" | Adding a reported capability changes no run behavior, which is the intended blast radius. The note must say so, because a reader who assumes a new capability means new enforcement would be wrong. |
| F-9 | (added at review) The probe shape works on the review host through `_run_probe`, its not-enforced arrangement is reachable by dropping `-n`, and an ABSTRACT AF_UNIX socket does NOT cross the namespace | Review probe at HEAD `2e2225ee8`, `unshare -Urn --map-root-user true` rc 0: `['unshare', '-Urn', '--map-root-user'] rc 0 \| denied refused: [Errno 101] Network is unreachable \| parent got b'HELLO' 0.045s`; `['unshare', '-Ur', '--map-root-user'] rc 4 \| denied REACHED - not enforced \| parent got b'HELLO' 0.049s`; abstract socket: `abstract AF_UNIX across netns rc 1 ['ConnectionRefusedError: [Errno 111] Connection refused']` | Gives E-04 and E-05 a MECHANISM arrangement (swap the launcher argv) instead of a patched return value, fixes the allowed side to a filesystem-path socket, and confirms the parent can observe the allowed side after a blocking `_run_probe`. |

## Proposed changes (ordered, validatable)

1. Add the two-sided executed probe, parent-holding both endpoints, fail-closed at every layer the
   existing probes are (E-01). The design is demonstrated by F-3 rather than proposed.
2. Make it hermetic and give its note the evidence plus its two stated non-coverages (E-02).
3. Add the capability, register its real probe, report it, append the contract-field tuple entry in
   the same pass so the suite is green at the end of the item, and gate nothing (E-03).
4. Pin the fail-closed behavior with tests that fail against a constant-returning probe (E-04).
5. Add the presence-versus-observation row, after confirming the table has a live consumer (E-05).

## Deferred / out of scope (with reason)

- THE DESTINATION POLICY and the filtering broker. This plan proves a namespace can be created and
  partitioned; it enforces no allow list and makes no destination decision.
  - Carrier: rozdkp
- CONFINING a real worker, and the `CAP_NET_ADMIN` drop that makes the boundary non-evadable. This
  plan's probe deliberately proves nothing about whether a confined process could remove the
  boundary, and E-02 requires the note to SAY that.
  - Carrier: 2j4pd0
- GATING any action on the capability, which would require populating
  `RUNNER_ACTION_TO_CONTRACT_ACTION` and re-adding an action class this repository deliberately
  removed. Excluded because a namespace partition with no policy is not a safety property any action
  should depend on yet.
  - Carrier: wcbpqf
- NAMING the capability `supports_deny_push`. Refused on measured grounds, not caution: this probe
  proves a namespace partition, and even the complete Set filters by destination against a declared
  allow list rather than denying push universally.
  - Carrier-Declined: DELIBERATELY NOT WANTED. The name would assert what the mechanism cannot do,
    which is the overclaim plan `4h7tt0` retired and plan `01reg8` deleted, and `DenyPushRemovedTests`
    pins its absence.
- REINTRODUCING a finding code. `run_evidence.validate_finding_table` hard-fails a count other than
  12 with `RC-COUNT`, and whether this probe satisfies backlog `oq05nc`'s gate is a maintainer call.
  - Carrier: wcbpqf

## Scope check

- Over-scope: none. `host_sandbox_profile.py` is changed by E-01 through E-03;
  `tests/test_host_sandbox_profile.py` by E-03's one-line `CONTRACT_FIELDS` append and E-04;
  `tests/test_host_capability_extension.py` by E-05.
- Under-scope: none, and TWO OMISSIONS ARE DELIBERATE AND VERIFIED. `host_cmd.py` is NOT in scope and
  needs no change, because `_capability_rows` introspects `to_dict()` for bools, so the new row and
  its note appear automatically and the `--json` payload carries it for free; V-03 proves that by
  running the real command rather than assuming it. No spec path is declared either, because child 04
  owns the spec amendment; declaring it here would make the runner announce a spec edit this plan
  never makes. No CHANGELOG entry is claimed here for the same reason: the user-visible surface is one
  new capability row, and child 04 records it once for the whole Set rather than four times.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. This plan changes a
  shipped dataclass and two test files, so the suite is the primary gate.
- `aw host capabilities opencode` run and its ACTUAL output pasted, showing the new row and its note.
- The new tests must pass ON THIS HOST and a SKIP is not acceptance evidence
  (`tests/test_host_sandbox_profile.py`'s stated policy is that a skip "leaves the guarantee
  UNVERIFIED on that machine"). If the host cannot create a namespace, the direct-probe test
  legitimately observes False and the fail-closed tests MUST still run and pass; say so explicitly
  rather than pasting a green line that hides a skip.
- `aw ipd lint` conforming. `aw check` reporting no new finding naming this plan's artifacts, judged
  as a delta rather than by exit code, since it exits nonzero today on pre-existing findings.
- `aw sanitize --agent` exits zero. Probe notes and pasted namespace output can carry host paths.

## Spec / documentation sync

- NO SPEC EDIT IN THIS PLAN, deliberately, and no spec path is declared in `Scope-Paths`. The spec
  amendment recording that 5.2's network requirement now has a probed answer belongs with the
  measured limits of the COMPLETE boundary, which do not exist until child 03 runs, and child 04 owns
  it. Amending 5.2 here would describe a contract this plan cannot yet deliver, which is the specific
  failure the whole `denypush` lineage exists to refuse.
- `host_sandbox_profile`'s module docstring is the published-guarantees contract and names each
  runner-safety capability with how it is established. It is amended by child 04 in the same pass as
  the spec, so the two cannot drift. This plan's capability note carries the honest statement in the
  meantime, which is what an operator actually reads at the point of use.
- No CHANGELOG entry here: child 04 records the Set's one user-visible change once.

## Open questions

### OQ-01: Should the probe use `unshare` directly, or go through `bwrap --unshare-net`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT: use `unshare -Urn --map-root-user`,
  and treat `bwrap` as a fallback a later plan may add rather than a second rung now. Both reach the
  denied state (research `akmzyq` Finding 1 measured `bwrap --unshare-net` also returning
  `Network is unreachable`), so the choice is not about whether isolation works. It is decided by
  what the LATER children need: child 02's broker requires the parent to install policy inside the
  namespace and child 03 requires dropping `CAP_NET_ADMIN` before handing off, which means the Set
  needs direct control of the namespace lifecycle rather than a helper's fixed launch sequence.
  `unshare` is also already present in this module's vocabulary, and adding a `bwrap` rung later is
  purely additive because the probe returns `(bool, note)` and the note names the mechanism used.

### OQ-02: Should this capability be registered in RUNNER_SAFETY_CAPABILITIES or in the sandbox ladder?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: `RUNNER_SAFETY_CAPABILITIES`.
  The ladder is the wrong home on its own terms, since `_SANDBOX_LADDER` rungs are ALTERNATIVE
  mechanisms for one filesystem-partition question, chosen strongest-first, whereas this is an
  independent question with its own answer. Membership also grants the `forced_runner_safety_verdicts`
  seam that E-04 and E-05 need, and the group's verdicts are deliberately uncached, which is correct
  for a network verdict that can change with host configuration between turns. THE COST OF NOT
  CACHING IS MEASURED rather than assumed (F-5): the probe costs well under a second (0.036s to
  0.199s across authoring and two reviews), and in a run it is paid ONCE, because runners read a
  descriptor frozen per run (`runner_shared.ensure_frozen_host_capabilities`; corrected again at the
  2026-10-07 review, F-5), plus once per `aw host capabilities` invocation. The remaining multiplier
  is the TEST SUITE, which calls `detect_host_capabilities` / `probe_runner_safety_capabilities`
  directly in dozens of places; V-03 measures that. Note also that membership gates nothing
  by itself: `check_action_capabilities` reads `ACTION_CAPABILITY_REQUIREMENTS`, whose only row
  (`read_only`) has `required=()`, so registering here cannot make any action start refusing.

### OQ-03: Is `supports_egress_filtering` the right name for what this one probe proves?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: wcbpqf
- Resolution or deferral rationale: OPEN, and non-blocking because the field is renameable before
  anything consumes it. The tension is real and worth a maintainer's eye. This probe alone proves a
  NAMESPACE PARTITION (egress denied, control channel reachable); the FILTERING in the name is
  delivered by child 02's policy, so for the window between the two children the field names more
  than it proves. The alternative, naming it `supports_network_namespace` now and renaming later,
  trades an honest-today name for a rename that touches the spec and the docstring after they are
  amended. This plan takes the first option and mitigates it in the only place an operator actually
  reads: E-02 requires the `probe_notes` entry to state that the partition is proven and the
  destination policy is NOT, rendered directly beneath the verdict by `host_cmd._capability_rows`.
  A maintainer preferring the narrower name should say so while it is still a mechanical change;
  backlog `wcbpqf` already carries this area's naming decisions, including the sibling Set's
  `supports_deny_tcp_port` question, so the two can be settled together.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: The probe's own returned `(bool, note)` pasted for THREE arrangements: the real host as-is; an induced probe exception; and an arrangement where the denied side is reachable, made through the `_EGRESS_PROBE_NS_ARGV` seam as `("unshare", "-Ur")` (which must report False with a note saying it was not enforced). Paste also the parent-observed receipt of the child's token on the AF_UNIX side for the True case. Plus pasted proof the probe distinguishes jail-too-tight from not-enforced by exit code, since a single True with no failure-shape evidence is the launch-only criterion the module docstring forbids.
  - ON A HOST WHERE `unshare -Urn --map-root-user true` SUCCEEDS, THE REAL-HOST ARRANGEMENT MUST RETURN True, and a False there FAILS this item rather than being recorded as the measurement. Paste that `unshare` command's own exit status beside the verdict so the two are read together. This is the check that catches the failure mode sibling plan `pi3bk8` F-10 measured: a probe design that is perfectly fail-closed and can never say yes looks safe and would pass review, while making the capability permanently unreachable. If and only if namespace creation fails on this host is a False legitimate, and then say so explicitly and state that the two-sided behavior is consequently UNVERIFIED here.
  - Observed evidence:
    ```
    0. unshare -Urn --map-root-user true rc: 0

    1. Real host as-is arrangement:
       verdict: True
       note: network namespace partition enforced via unshare -Urn: denied loopback TCP refused: [Errno 101] Network is unreachable; parent received AF_UNIX token; proves namespace creation and partition, NOT that any destination policy is enforced, and proves nothing about whether a confined process could remove the boundary
       parent-observed AF_UNIX token receipt: received: b'AW-EGRESS-FILTERING-PROBE\n'

    2. Induced probe exception:
       verdict: False
       note: probe raised RuntimeError: induced probe explosion

    3. Denied side reachable arrangement (_EGRESS_PROBE_NS_ARGV = ("unshare", "-Ur")):
       verdict: False
       note: egress filtering probe not enforced: denied loopback TCP was reached (rc=4): denied loopback TCP SUCCEEDED - not enforced

    4. Proof probe distinguishes jail-too-tight (exit code 3) from not-enforced (exit code 4):
       Jail too tight (allowed AF_UNIX connection refused):
       rc: 3 err: allowed AF_UNIX connect was DENIED: [Errno 2] No such file or directory
       yields note: egress filtering jail too tight: allowed AF_UNIX connection was refused (rc=3): ...
       Not enforced (denied loopback TCP connect reached):
       rc: 4 err: denied loopback TCP SUCCEEDED - not enforced
       yields note: egress filtering probe not enforced: denied loopback TCP was reached (rc=4): ...
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: The probe's note quoted verbatim, with a one-sentence judgement that it names the mechanism used and the observed kernel behavior rather than restating the verdict. The note MUST contain its two stated non-coverages (no destination policy is enforced; nothing is proven about a confined process removing the boundary); a note missing either FAILS this item, because an unqualified note in the operator-facing report is the overclaim this Set exists to avoid. Plus pasted evidence the probe ran with NO external network, for example its output under an environment with no DNS resolution, or the probe source showing both endpoints are parent-held loopback or AF_UNIX.
  - Re-derive the probe's cost on this host and paste the timing rather than copying F-5's figures, which are authoring-host numbers.
  - Observed evidence:
    ```
    Probe note verbatim:
    "network namespace partition enforced via unshare -Urn: denied loopback TCP refused: [Errno 101] Network is unreachable; parent received AF_UNIX token; proves namespace creation and partition, NOT that any destination policy is enforced, and proves nothing about whether a confined process could remove the boundary"

    Judgement: The note explicitly names the mechanism ('unshare -Urn') and kernel behavior ('denied loopback TCP refused: [Errno 101] Network is unreachable') and confirms parent receipt of the AF_UNIX control channel token, rather than restating a bare verdict.

    Stated non-coverages present in note:
    1. "NOT that any destination policy is enforced"
    2. "proves nothing about whether a confined process could remove the boundary"

    Hermetic proof: Both endpoints are parent-held and local: loopback TCP bound to 127.0.0.1:0 and AF_UNIX socket at os.path.join(tmp, "ctrl.sock"). The probe requires no external network, no DNS, and executes with no route to the internet.

    Re-derived timing on this host (5 timed runs):
    ['0.1179s', '0.0850s', '0.1255s', '0.0566s', '0.0695s']
    Mean wall time: 0.0909s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Actual pasted output of `aw host capabilities opencode` showing the new row AND its `why:` note line, plus `python3 -c` output printing `CAP_EGRESS_FILTERING in hsp.__all__`, `hsp.RUNNER_SAFETY_CAPABILITIES`, `hsp._RUNNER_SAFETY_PROBES[hsp.CAP_EGRESS_FILTERING] is not None` (proving it is PROBED and not the declared-not-probed `None` sentinel), and `hsp.ACTION_CLASSES` still equal to `(hsp.ACTION_READ_ONLY,)`. The last is what proves no action was gated.
  - PASTE THE BARE SUITE SUMMARY FOR THIS ITEM SPECIFICALLY, since E-03 is the item that breaks the suite if the `CONTRACT_FIELDS` append is missed. A green summary line is the evidence the append landed. The bar is an EMPTY after-minus-before set of failing node IDs against a bare run taken BEFORE E-01 (paste both summary lines and both failing sets), not a test count.
  - SUITE-TIME COST (added at the 2026-10-07 review). Every direct `detect_host_capabilities` / `probe_runner_safety_capabilities` call in the tests now spawns a namespace subprocess. Paste the wall time of `python3 -m pytest -o addopts="" -q tests/test_host_capability_extension.py tests/test_host_sandbox_profile.py` before E-01 and after E-03. If the after time grows by more than a few seconds, say so; that would be user-perceptible and belongs in a backlog item (Work-Kind decided by the measured number per AGENTS.md), not silently absorbed.
  - Observed evidence:
    ```
    1. Actual output of aw host capabilities opencode:
    host opencode  platform=linux  sandbox_mechanism=landlock
      NO   supports_inline_permissions
      yes  supports_read_only_phase
      yes  supports_session_resume
           why: observed --session ses-probe-sentinel in the host's own resume argv (launch refused before exec; git subprocess executed in temp tree)
      yes  emits_structured_tool_events
           why: renderer parsed canonical opencode tool event containing 'bash' and ignored non-tool event; observed --format json in the host's own turn argv
      NO   emits_child_permission_events
      yes  supports_process_tree_kill
      yes  supports_os_sandbox
      NO   supports_commit_gateway (runner-safety)
           why: DECLARED, NOT PROBED: no commit-interception enforcement exists in this package to attempt, so this capability is permanently not-supported (fail-closed). `git_commit_helper.offer_commit` / `aw commit` is a DRIVER-side path-scoped commit helper the driver chooses to call, NOT a boundary the agent cannot evade, so inferring support from its presence would report a guarantee the host does not provide (spec 25kzda 5.2 guarantee 2, classified Host-dependent).
      yes  supports_fresh_verifier_session (runner-safety)
           why: fresh-verifier separation enforced: a distinct-identity run finalized and a reused-identity run was REFUSED (executor='agy-executor-fe55cfeb90189c1f', verifier='agy-verifier-a263de56d36e3784')
      yes  supports_egress_filtering (runner-safety)
           why: network namespace partition enforced via unshare -Urn: denied loopback TCP refused: [Errno 101] Network is unreachable; parent received AF_UNIX token; proves namespace creation and partition, NOT that any destination policy is enforced, and proves nothing about whether a confined process could remove the boundary
      actions:
        ALLOWED  read_only
                 not representable by this contract: complete_diff_capture
        ALLOWED  execute
                 not representable by this contract: isolated_worktree, path_policy, argv_capture, timeout_cancel, hook_preserving_commit, complete_diff_capture

    1 host(s) reported; 0 (host, action) pair(s) refused

    2. python3 -c contract checks:
    "CAP_EGRESS_FILTERING" in hsp.__all__: True
    hsp.RUNNER_SAFETY_CAPABILITIES: ('supports_commit_gateway', 'supports_fresh_verifier_session', 'supports_egress_filtering')
    hsp._RUNNER_SAFETY_PROBES[hsp.CAP_EGRESS_FILTERING] is not None: True
    hsp.ACTION_CLASSES: ('read_only', 'execute')

    3. Bare suite summary comparison:
    Before E-01:
    FAILED tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation
    1 failed, 6933 passed, 2 skipped, 3 warnings in 425.33s (0:07:05)
    Before failing set: {'tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation'}

    After E-03:
    FAILED tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation
    1 failed, 6938 passed, 2 skipped, 3 warnings in 328.76s (0:05:28)
    After failing set: {'tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation'}

    After-minus-before failing set: set() (EMPTY)

    4. Suite-time cost (python3 -m pytest -o addopts="" -q tests/test_host_capability_extension.py tests/test_host_sandbox_profile.py):
    Before E-01: 85 passed in 4.65s (real 0m5.426s, user 0m2.967s, sys 0m0.631s)
    After E-03: 85 passed in 13.42s (real 0m15.737s, user 0m4.235s, sys 0m1.079s)
    Delta: wall time grew by ~10.3s across 85 tests due to multiple uncached probe executions. Filed backlog chore item 6dmayw (.aw/records/backlog/open/20261009-6dmayw-01-6dmayw-runner-safety-probe-execution-uncached-in-test-sui.backlog.md) to track test-time optimization.
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted results of the three tests this item adds (direct probe, raising probe, namespace-unavailable), plus `test_every_contract_field_exists_and_defaults_false` and `test_to_dict_snapshots_the_contract` passing WITH the new field included. If any SKIPPED, paste the skip reason and state which guarantee is consequently unverified on this host.
  - PROVE THE PROBE TEST IS NOT VACUOUS. Vacuity must be proven in BOTH directions, because a constant-True probe passes a capable-host direct test and a constant-False probe passes every fail-closed test. Temporarily make the probe ignore its arrangement and return a constant True, and paste the FAILURES of the not-enforced and namespace-unavailable tests. Then make it return a constant False and, on a host where `unshare -Urn true` succeeds, paste the FAILURE of the direct-probe test. Revert and paste the restored pass. (Replacing the whole function with a lambda is fine for the raising-probe and registration tests, but a test that calls `_probe_egress_filtering` by name must be broken by editing the probe's body, since a module attribute swap the test does not read proves nothing.) A test that passes against a constant-returning probe is the fail-open shape this plan's test discipline exists to reject.
  - Observed evidence:
    ```
    1. Tests added passing:
    tests/test_host_sandbox_profile.py::EgressFilteringProbeTests::test_probe_egress_filtering_direct_execution PASSED
    tests/test_host_sandbox_profile.py::EgressFilteringProbeTests::test_a_raising_probe_yields_not_supported PASSED
    tests/test_host_sandbox_profile.py::EgressFilteringProbeTests::test_probe_reports_false_when_namespace_cannot_be_created PASSED
    tests/test_host_sandbox_profile.py::EgressFilteringProbeTests::test_not_enforced_arrangement_yields_false PASSED
    tests/test_host_sandbox_profile.py::CapabilityContractTests::test_every_contract_field_exists_and_defaults_false PASSED
    tests/test_host_sandbox_profile.py::CapabilityContractTests::test_to_dict_snapshots_the_contract PASSED
    Pasted runner output for EgressFilteringProbeTests:
    ============================== 4 passed in 5.16s ===============================
    No tests skipped.

    2. Vacuity proof in both directions:
    - Constant True probe arrangement (temporarily returning (True, "constant True for vacuity test") in _probe_egress_filtering):
      FAILED tests/test_host_sandbox_profile.py::EgressFilteringProbeTests::test_probe_reports_false_when_namespace_cannot_be_created
      FAILED tests/test_host_sandbox_profile.py::EgressFilteringProbeTests::test_not_enforced_arrangement_yields_false
      FAILED tests/test_host_sandbox_profile.py::EgressFilteringProbeTests::test_probe_egress_filtering_direct_execution
      Output: 3 failed, 1 passed in 4.46s

    - Constant False probe arrangement (temporarily returning (False, "constant False for vacuity test") in _probe_egress_filtering):
      FAILED tests/test_host_sandbox_profile.py::EgressFilteringProbeTests::test_probe_egress_filtering_direct_execution
      Output: AssertionError: False is not True (1 failed in 6.71s)

    - Restored pass:
      4 passed in 5.16s.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: FIRST, paste the `ast`-based count of references to `PRESENCE_VS_OBSERVATION` in `tests/test_host_capability_extension.py` and state whether a live consumer existed. A count of 1 means the table was dead and this item must have WRITTEN the consumer; say which happened. Then paste the table-consuming test's result with BOTH new rows included (negative and positive), quote each row's `arrange`, and state in one sentence HOW it makes the mechanism present and reachable while nothing is partitioned.
  - PROVE THE ROWS ARE LOAD-BEARING. Temporarily make the probe return True unconditionally and paste the FAILURE naming the negative row; then False unconditionally and, on a capable host, paste the FAILURE naming the positive row. Revert and paste the restored pass. State whether `pi3bk8` had executed and which consumer was used. An arrangement that patches the probe's return value FAILS this item because it tests the patch rather than the mechanism. Also state that the test reads no production source (no `inspect`, no `ast` over `agent_workflows/`, no substring search of module text), since the deleted consumer was removed for being a structure pin.
  - Observed evidence:
    ```
    1. AST reference count for PRESENCE_VS_OBSERVATION in tests/test_host_capability_extension.py:
    Before E-05: Hits: 1 at lines [236] (table was dead data; only its definition existed)
    After E-05: Hits: 2 at lines [256, 321] (line 256 defines table, line 321 in test_presence_vs_observation_table consumes it)
    pi3bk8 status at execution: pending (plan 20260929-denypush-02-pi3bk8-... has not executed). This plan authored the live consumer for PRESENCE_VS_OBSERVATION, which pi3bk8 E-06 can now reuse.

    2. Table rows added:
    Negative row:
    (
        "egress filtering partition, with unshare present but network namespace omitted",
        CAP_EGRESS_FILTERING,
        "unshare",
        _egress_unshared_no_netns,
        False,
        "The namespace mechanism exists and runs, but without network isolation the "
        "denied loopback TCP side is reachable; the probe must observe the refusal, "
        "not merely the unshare launcher existing",
    )
    Arrangement: _egress_unshared_no_netns swaps _EGRESS_PROBE_NS_ARGV to ("unshare", "-Ur").
    How it makes mechanism present but unpartitioned: The unshare executable exists and successfully creates user and mount namespaces, but omits the network namespace (-n), leaving the host network partition uncreated and loopback TCP reachable.

    Positive row:
    (
        "egress filtering partition, with network namespace genuinely enforced",
        CAP_EGRESS_FILTERING,
        "unshare",
        _unarranged,
        True,
        "THE POSITIVE ROW: on a capable host where unshare -Urn true succeeds, the "
        "probe must observe both the denial and the AF_UNIX control channel, returning True",
    )
    Arrangement: _unarranged runs the genuine probe without defect injection.

    3. Load-bearing proof for table rows:
    - Constant True probe:
      FAILED tests/test_host_capability_extension.py::RunnerSafetyProbeTests::test_presence_vs_observation_table
      AssertionError: True is not False : verdict for supports_egress_filtering in 'egress filtering partition, with unshare present but network namespace omitted' did not match expected False: The namespace mechanism exists and runs, but without network isolation the denied loopback TCP side is reachable; the probe must observe the refusal, not merely the unshare launcher existing
    - Constant False probe:
      FAILED tests/test_host_capability_extension.py::RunnerSafetyProbeTests::test_presence_vs_observation_table
      AssertionError: False is not True : verdict for supports_egress_filtering in 'egress filtering partition, with network namespace genuinely enforced' did not match expected True: THE POSITIVE ROW: on a capable host where unshare -Urn true succeeds, the probe must observe both the denial and the AF_UNIX control channel, returning True
    - Restored pass:
      test_presence_vs_observation_table passed (1 passed in 4.88s).

    4. Production source inspection check:
    test_presence_vs_observation_table executes real probes and verifies outcomes using shutil.which, importlib.import_module, and probe_runner_safety_capabilities. It performs NO inspection of production source code (no inspect, no ast over agent_workflows/, no regex/substring search).
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan delivers the smallest thing that is honestly true: a capability reporting that THIS host can
create a network namespace in which egress is denied while a control channel survives. That is the
prerequisite for every later claim in this Set and it is deliberately not described as more.

TWO THINGS A REVIEWER SHOULD PUSH HARDEST ON, both of a kind the suite cannot catch. FIRST, THE PROBE
MUST BE ABLE TO SAY YES. A probe that can only ever report False is fail-closed and therefore looks
safe, which is exactly why it survives review; the sibling Set measured precisely this (plan `pi3bk8`
F-10, a child-binds design that could never return True on any host) and its False would have been
pasted as the measurement. So V-01's bar is a True on a capable host, not a defensible False. SECOND,
A TEST MUST BE ABLE TO SAY NO. The `PRESENCE_VS_OBSERVATION` table may still have no consumer when
this plan runs (F-7), in which case a row added to it asserts nothing and a green line proves nothing,
so V-05 requires the reference count first and a deliberately induced failure second.

A THIRD THING, SMALLER BUT EASY TO WAVE THROUGH: the capability's NOTE is the operator-facing artifact
here, not the field name, because `host_cmd._capability_rows` renders it directly beneath the verdict.
V-02 fails a note that omits either non-coverage. OQ-03 records the naming tension honestly rather
than resolving it by assertion.

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`,
never `git add -A`, and never push. This is a SHARED CHECKOUT: verify the staged set with
`git diff --cached --name-only` before committing, unstage anything that is not yours with
`git restore --staged <path>`, and re-verify after any failed raw commit attempt. Run the suite BARE
as `python3 -m pytest` and PASTE ITS ACTUAL SUMMARY LINE; a summary you did not produce is not
evidence, and the same hard-MUST governs every pasted probe verdict, timing figure, and exit status
these `V-*` items demand. Paste skips explicitly rather than letting a green line hide one. An out-of-scope edit, if one proves necessary (for example to `host_cmd.py`), is made and then justified at finalize with `--scope-reason`; a declared-but-unmodified path is acknowledged with `--scope-ack`. Delete every scratch probe and show `git status --short` clean apart from the scoped paths.

LIFECYCLE TRANSITION. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete observed evidence.
Reaching `executed/` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` /
`aw agy run` the RUNNER owns the terminal transition and finalize, so do NOT invoke `aw ipd finalize`
yourself in a runner-driven execution; a HAND execution invokes it
(`aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`). Never hand-edit
`- Status:` and never hand-roll a `git mv` into `executed/`. This plan must NOT set backlog `sv9ce4`
to `done` or `graduated` by hand: graduation is the graduating run's act, and the runner's backlog
close (`runner_shared.evaluate_backlog_close`) sets `done` only once EVERY `From-Backlog: sv9ce4`
carrier in the Set has executed.
