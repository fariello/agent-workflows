# IPD: Add a probed supports_deny_tcp_port capability proving TCP port denial by attempt

- Date: 2026-09-29
- Kind: child
- Concern: Spec `25kzda` 5.2 requires a host descriptor that answers, from probe evidence, whether the host can deny push-capable network routes. No capability answers it today: `supports_deny_push` was removed by plan `01reg8` precisely because it was declared and never probed. The measured result (research `uq4y6q`) is that kernel TCP denial IS provable but is port-granular, so the honestly-probable claim is narrower than "deny push" and must be named for what it proves.
- Scope: Add ONE new capability to `HostSandboxCapabilities`, `supports_deny_tcp_port`, decided by an EXECUTED two-sided Landlock network probe, reported through the existing `aw host capabilities` surface, and extend `landlock_bootstrap_source` to carry network rules. The capability gates NO action and reintroduces NO finding code. It must NOT be named `supports_deny_push`, because it does not prove push denial.
- Scope-Paths: agent_workflows/host_sandbox_profile.py, tests/test_host_sandbox_profile.py, tests/test_host_capability_extension.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, CHANGELOG.md
- Item-Dependencies: executed:x2dwu5
- Status: approved
- Readiness: go-pending-approval
- From-Spec: 25kzda
- Work-Kind: feature
- Priority: low
- From-Backlog: oq05nc
- Set: denypush
- Order: 2
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: pi3bk8
- Approval: 2026-10-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-901..PR-906 FIXED (round 2)
- 2026-10-07 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901 (HIGH, fixed: E-02 required the denied connect fail with EPERM, but Landlock returns EACCES/errno 13, measured; a literal EPERM check makes the probe never True), PR-902 (MEDIUM, fixed: E-08/E-09 said 'through the seam' but no ABI or allowed-port seam existed; forced_runner_safety_verdicts would make E-09 vacuous; E-02 now specifies both, E-08 arrangement measured reachable), PR-903 (MEDIUM, fixed: E-06 must coordinate the shared PRESENCE_VS_OBSERVATION consumer with nxh5s4), PR-904 (LOW, fixed: F-12/OQ-02 call-frequency stale, runners freeze the descriptor per run), PR-905 (LOW, fixed: gate surfaces l4vw9o OQ-01 ship-at-all at the point of approval), PR-906 (LOW, fixed: gate claimed oq05nc is graduated; it is open; close ownership named). Host Landlock ABI 4. Lint clean at author and review-finalize. Record: `.aw/records/reviews/20260930-denypush-02-pi3bk8-add-a-probed-supports-deny-remote-ssh-push-capability-provin.review.md` Round 2.
- 2026-10-07 to-review (aw set): returned to review: Set-level checks owned by wzhe4n E-03/E-04 (runs last); carrier sv9ce4 already exists; coverage pass recorded
- 2026-10-06 draft (aw set): demoted approved -> draft: APPROVAL WITHDRAWN: returned to authoring by gradcover 52opph: uncovered obligation: - THE CARRIER OUTLIVES THE SET. Backlog `sv9ce4` is filed before any child runs, so the unbuilt half
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: APPROVE WITH REVISIONS APPLIED; PR-801..PR-811 all fixed

- 2026-09-30 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801 (BLOCKER, fixed), PR-802 (HIGH, fixed), PR-803 (HIGH, fixed), PR-804 (MEDIUM, fixed), PR-805 (MEDIUM, fixed), PR-806 (MEDIUM, fixed), PR-807 (MEDIUM, fixed), PR-808 (LOW, fixed), PR-809 (LOW, fixed), PR-810 (LOW, fixed), PR-811 (LOW, fixed). Findings recorded in `.aw/records/reviews/20260930-denypush-02-pi3bk8-add-a-probed-supports-deny-remote-ssh-push-capability-provin.review.md`. I BUILT THE PROBE THIS PLAN SPECIFIES rather than reading research `uq4y6q`, and the authored design CANNOT WORK. PR-801: E-02 said "the child binds a loopback listener, applies a ruleset allowing only that listener's port", but `landlock_bootstrap_source` restricts BEFORE it `execv`s, so every allowed port is fixed while the child does not exist. Measured: with only port 40001 allowed and `restrict_self` applied, the process bound `127.0.0.1:56659` fine (bind is unrestricted, only `CONNECT_TCP` is handled) and connecting to its OWN socket gave `[Errno 13] Permission denied`. The ALLOWED half therefore always fails, so the probe returns False on a fully capable host: fail-CLOSED, which is why it would have survived review, and which would have made the capability permanently unreachable while the False was pasted as "the measurement". I then DEMONSTRATED the parent-binds design works (parent listeners 46623/46745, `rc: 0`, `denied connect refused: [Errno 13] Permission denied`), so E-02 now specifies it and V-02 requires a True on an ABI >= 4 host. PR-802: E-06 targeted the `PRESENCE_VS_OBSERVATION` table, which has had NO CONSUMER since commit `80db6750` deleted `test_no_runner_safety_probe_infers_support_from_helper_presence`; an `ast` walk finds exactly one reference, its own assignment, and the table's comment still claims a `_helper_exists` that exists nowhere. A fourth row plus a green suite line would have been evidence of nothing, so E-06 now restores the consumer FIRST and E-08 adds the row. PR-803: applying E-03's edits alone leaves the suite RED (`1 failed, 73 passed`, `AssertionError: 'supports_deny_tcp_port' not found in (...)`) because `test_new_contract_fields_and_defaults` asserts every `RUNNER_SAFETY_CAPABILITIES` member is in `CONTRACT_FIELDS`; the tuple append moved into E-03, making it `74 passed`. Also fixed: the credential row repeated the exact "already built and shipped" overclaim Order 01's own review corrected as its PR-701 (`pinned_child_env` is `os.environ.copy()`, so no env-carried token is withheld), `CHANGELOG.md` was warranted but undeclared, OQ-03 named sibling plan `wzhe4n` as a carrier for product work it forbids itself (correct carrier: backlog `sv9ce4`), V-07's `grep -c REFUSED` returns 1 on the current tree (the fresh-verifier note says "was REFUSED") where the test asserts the two-space form, and V-05 asked for `probe() == probe()`, vacuous against a constant. OQ-01 RESOLVED at review (keep the short name; the direction ambiguity is real, both rights are separately accepted by this kernel, but `_capability_rows` renders the note beneath every row so direction is read at the point of use). E-06 split into E-06/E-08/E-09 after `IPD-Z602` flagged my own rewrite as multi-concern. `aw ipd lint --phase review-finalize` conforming, zero findings.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `oq05nc`. Depends on Order 01 landing the measurement and the spec amendment first.
- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give spec `25kzda` 5.2's network requirement its first PROBED answer: a capability that is True only
when the kernel actually refused a TCP connect to a denied port while permitting one to an allowed
port, on this host, in this process tree. Name it for exactly what the probe proves
(`supports_deny_tcp_port`) so nothing in the descriptor can be read as a push-denial guarantee the
mechanism cannot deliver.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the mechanism

- [x] E-01 Extend `host_sandbox_profile.landlock_bootstrap_source` to accept an optional set of allowed TCP ports and emit a ruleset that handles `LANDLOCK_ACCESS_NET_CONNECT_TCP` alongside the filesystem rights it already handles. The generated source currently packs the ruleset attr as `struct.pack("=QQ", ALL, 0)`, whose literal `0` IS `handled_access_net`; set it to the connect-TCP bit when ports are requested and add one `LANDLOCK_RULE_NET_PORT` rule per allowed port. Guard on the reported ABI: network rules require ABI >= 4, so on a lower ABI the bootstrap must add no network rule and must NOT claim network handling. Default the parameter so every existing caller is byte-unchanged.
  - Depends on: none
  - Expected outcome: `landlock_bootstrap_source(...)` with no port argument emits source identical to today's; with ports it emits a ruleset handling connect-TCP. Existing callers and existing tests are unaffected.
  - Execution state: performed

- [x] E-02 Add `_probe_deny_tcp_port`, a two-sided executed probe modeled on `_probe_landlock` and holding the same standard `_denial_checker_source` sets for the filesystem: it must prove a DENIAL and not a launch. THE PARENT BINDS BOTH LISTENERS, NOT THE CHILD, and this is a correctness requirement rather than a style choice (see the measured refutation below). The parent binds two loopback listeners on ephemeral ports, passes only the FIRST port to the network-extended `landlock_bootstrap_source`, and the bootstrap restricts itself and `execv`s a checker that (a) connects to the allowed port and requires success, and (b) connects to the second (unallowed) port and requires the kernel to refuse with `EACCES` (errno 13, `PermissionError`, "Permission denied"), NOT `EPERM` (errno 1), which this item originally named and which Landlock does not return for a denied connect (corrected at the 2026-10-07 review, measured: with connect-TCP handled and one port allowed, `allowed connected` / `denied errno 13 EACCES`; F-10's own measurement already read `[Errno 13] Permission denied`). Test `isinstance(exc, PermissionError)` or `exc.errno == errno.EACCES`; a check against `errno.EPERM` would make the probe return False on every capable host. The parent must keep both listening sockets OPEN for the child's lifetime, since a closed listener yields `ECONNREFUSED` (errno 111) and not the `EACCES` that distinguishes a kernel denial from a dead port. Exit codes must distinguish the three failure shapes the way `_denial_checker_source` does: allowed-connect-denied (jail too tight), denied-connect-succeeded (not enforced), and success. Route the subprocess through `_run_probe` so any nonzero exit, exception, or timeout maps to False, and honor `_PROBE_TIMEOUT_SECONDS` and the `CERTIFIED_PLATFORM` gate (applied inside the probe itself, because `detect_host_capabilities` calls `probe_runner_safety_capabilities` under `plat == running_platform` BEFORE its own certified-platform check).
  - TWO TEST SEAMS, required by E-08 and E-09 (added at the 2026-10-07 review, because neither existed and both items said "through the seam" without naming one). (i) ABI: read the Landlock ABI IN THE PARENT through a small module-level helper (for example `_landlock_abi() -> int`, the same `syscall(444, NULL, 0, LANDLOCK_CREATE_RULESET_VERSION)` the bootstrap already issues) and return `(False, note)` naming the reported ABI when it is below 4, BEFORE launching anything; E-09 patches that helper. The bootstrap keeps its own in-child ABI guard (E-01) as the second layer. (ii) ALLOWED PORTS: build the allowed-port set through a module-level hook (for example `_deny_tcp_probe_allowed_ports(allowed, denied) -> tuple` returning `(allowed,)` in production); E-08 swaps it to return `(allowed, denied)`, which really applies a ruleset that really refuses nothing. Measured at review: with BOTH ports in the ruleset, `allowed connected` / `denied-but-also-allowed connected`, so that arrangement reaches the not-enforced exit code. Neither seam patches the probe's return value.
  - THE "CHILD BINDS ITS OWN LISTENER" DESIGN IS IMPOSSIBLE, MEASURED AT REVIEW, and this bullet exists because that is what this item originally specified. `landlock_bootstrap_source` applies the ruleset BEFORE it `execv`s, so every allowed port must be chosen while the child does not yet exist. A child that binds afterwards gets an arbitrary ephemeral port that is NOT the allowed one, so its own listener is unreachable to it. Measured: with only port `40001` allowed and `restrict_self` applied, the process then bound `127.0.0.1:56659` successfully (bind is unaffected, since only `CONNECT_TCP` is handled) and connecting to that very socket returned `[Errno 13] Permission denied`. The ALLOWED half of the two-sided test therefore always fails and the probe would report False on a fully capable host: a fail-CLOSED wrong answer, which is safe but makes the capability permanently unreachable and the positive test unpassable. THE PARENT-BINDS DESIGN WAS DEMONSTRATED TO WORK on this host, which is the standard `/plan-review` Step 3.1 sets for a HOW resolution: with the parent holding listeners on `46623` (allowed) and `46745` (denied), the extended bootstrap plus checker exited `rc: 0` with stderr `denied connect refused: [Errno 13] Permission denied`, i.e. the allowed connect SUCCEEDED and the denied one was refused by the kernel in one run.
  - Depends on: E-01
  - THE NOTE MUST NAME THE DIRECTION AND THE GRANULARITY, which OQ-01's resolution rests on. It states that what was proven is an OUTBOUND connect denial (`LANDLOCK_ACCESS_NET_CONNECT_TCP`, not the separate bind-TCP right, both of which this kernel accepts as handled rights: measured at review), that it is PER PORT with no address component, and that it therefore does not separate a git remote from any other destination on the same port. The note is where an operator meets the limit, because `host_cmd._capability_rows` renders it directly beneath the verdict row.
  - Expected outcome: A probe returning `(bool, note)` that is True only on proven two-sided denial, and False with an explanatory note on every other outcome including ABI < 4 and non-Linux. On a host reporting ABI >= 4 with Landlock networking enforced, the probe must return True; a design that cannot return True on such a host has not met this item.
  - Execution state: performed

### Task group 2: the contract surface

- [x] E-03 Add the capability `supports_deny_tcp_port` to `HostSandboxCapabilities` defaulting False, add the `CAP_DENY_TCP_PORT` constant, register it in `RUNNER_SAFETY_CAPABILITIES`, wire `_RUNNER_SAFETY_PROBES[CAP_DENY_TCP_PORT] = _probe_deny_tcp_port` (a real probe, NOT the `None` sentinel that marks declared-not-probed), and export the constant in `__all__`. Set the verdict and its `probe_notes` entry in `detect_host_capabilities` alongside the existing probed capabilities. Do NOT add it to `ACTION_CAPABILITY_REQUIREMENTS` and do NOT add an action class: `ACTION_CLASSES` stays `(ACTION_READ_ONLY,)`. IN THE SAME PASS, append `"supports_deny_tcp_port"` to `tests/test_host_sandbox_profile.py`'s `CONTRACT_FIELDS` tuple, because THIS ITEM BREAKS THE SUITE WITHOUT IT: `test_new_contract_fields_and_defaults` iterates `RUNNER_SAFETY_CAPABILITIES` and asserts every member is present in `CONTRACT_FIELDS`, which it imports from the other test module. Measured at review by applying exactly this item's edits and nothing else: `1 failed, 73 passed`, with `AssertionError: 'supports_deny_tcp_port' not found in (...)`; adding the tuple entry makes it `74 passed`. E-05 still owns the rest of that file's coverage; only the one-line tuple append moves here, because a plan whose middle item leaves the suite red cannot honestly run the bare suite as its own gate.
  - Depends on: E-02
  - Expected outcome: `aw host capabilities` reports the new row automatically (`host_cmd._capability_rows` introspects `caps.to_dict()` for bool values rather than reading a name list), with a `probe_notes` entry recording the evidence. No action is gated, so no run behavior changes. The suite is GREEN at the end of this item, not merely at the end of the plan.
  - Execution state: performed

- [x] E-04 Amend `host_sandbox_profile`'s module docstring: add the new capability to the runner-safety bullet list describing how each is established, stating it is PROBED by attempt and two-sided; update the prose that currently counts the fields ("Two fields and a preflight close that"); and state the port-granularity limit explicitly in the bullet, so a reader of the contract cannot mistake it for push denial. Also state that the capability gates no action today, which is the same honest limit the docstring already records for the preflight.
  - Depends on: E-03
  - Expected outcome: The published-guarantees contract describes the new capability, what it proves, and what it does NOT prove, with the count prose corrected.
  - Execution state: performed

### Task group 3: tests, including the anti-overclaim guards

- [x] E-05 Pin the new probe's fail-closed behavior in `tests/test_host_sandbox_profile.py`. The `CONTRACT_FIELDS` append itself moved to E-03 (see that item's measured reason: without it E-03 leaves the suite red), so this item OWNS THE TESTS THAT USE the tuple entry rather than the entry. That tuple, not dataclass introspection, drives `test_every_contract_field_exists_and_defaults_false` and `test_to_dict_snapshots_the_contract`, and its own comment warns that "a field absent from it carries NO default-False or snapshot guarantee while the suite stays green", so confirm both now cover the new field. Then add: a test asserting a RAISING probe yields False with the note recording the exception; and a test that drives `_probe_deny_tcp_port` DIRECTLY and asserts the returned `(bool, note)` pair, so the probe is exercised rather than only its registration. MIRROR `test_a_raising_probe_yields_not_supported` IN `tests/test_host_capability_extension.py`, NOT the similarly named `test_a_raising_probe_is_treated_as_unavailable` in this file, which the original wording pointed at. Both symbols exist (verified at review) and they exercise DIFFERENT seams: the one named here patches `_RUNNER_SAFETY_PROBES` and asserts the note contains `"probe raised RuntimeError"`, which is the path a runner-safety capability actually takes, while the other patches `_SANDBOX_LADDER` and `_SANDBOX_PROBE_CACHE`, which the new capability never touches. Copying the sandbox-ladder shape would test a mechanism this capability is deliberately not registered in (OQ-02).
  - DO NOT WRITE "the reported verdict equals a forced re-run of the probe", which the original wording asked for and which is VACUOUS: `probe_runner_safety_capabilities` is uncached, so it re-runs the same probe function and the assertion reduces to `probe() == probe()`. That passes for a probe returning a constant, which is the fail-open shape this area's whole test discipline exists to reject. Assert the verdict against an ARRANGED kernel outcome instead (E-06 supplies the arrangement), or assert the probe's own returned note names the evidence.
  - Depends on: E-03
  - Expected outcome: The new field carries the same default-False and snapshot coverage every other contract field has, and the probe's fail-closed behavior is pinned by tests that would fail if the probe returned a constant.
  - Execution state: performed

- [x] E-06 Restore a LIVE CONSUMER for `tests/test_host_capability_extension.py`'s `PRESENCE_VS_OBSERVATION` table, which is currently dead data. THE TABLE ASSERTS NOTHING TODAY, measured at review: an `ast` walk of that file for every `Name`/`Attribute` reference to `PRESENCE_VS_OBSERVATION` returns exactly `[('name', 235)]`, its own assignment, because commit `80db6750` ("test: delete 366 tests that pinned code structure instead of behaviour") deleted `test_no_runner_safety_probe_infers_support_from_helper_presence`, the sole consumer, and left the data behind. Its comment still claims "`_helper_exists` is asserted per row" while no such symbol exists anywhere in the repository. Write the consuming test: iterate the table, and for each row assert the named helper is importable and callable (so a row cannot pass because its witness vanished), run `probe_runner_safety_capabilities` under the row's `arrange` context manager, and assert the returned verdict equals the row's expected value. This is a BEHAVIORAL test (it drives the prober and asserts returned verdicts), not a source-structure pin, so it conforms to AGENTS.md P16. Restore NO part of the deleted test that read source text, counted symbols, or scanned `sys.modules` for an import fingerprint: those are why it was deleted, and reviving them would re-create the defect that commit removed.
  - Depends on: E-03
  - COORDINATE WITH `nxh5s4` (Set `netnsfilter`, Order 01). Its E-05 writes a consumer for this SAME table if none exists, and adds its own capability's rows. FIRST re-derive whether a consumer already exists (a reference to `PRESENCE_VS_OBSERVATION` beyond its assignment): if `nxh5s4` landed first, reuse its consumer and skip writing one; otherwise write it so `nxh5s4` can reuse it. Record which happened in V-06. The table's witness column is `(module, attribute)`-shaped, while `nxh5s4`'s row witnesses an executable; whichever plan writes the consumer must accept both shapes.
  - Expected outcome: The three EXISTING rows regain the guarantee they were written to carry, verifiable by inverting a probe and seeing the new test fail. This item adds no row of its own, deliberately: the consumer must be proven live before a row is worth adding to it.
  - Execution state: performed

- [x] E-08 Add the new capability's row to `PRESENCE_VS_OBSERVATION`, now that E-06 gave the table a consumer. The row's `arrange` must make the kernel mechanism PRESENT AND REACHABLE while the denial is NOT observed, which is the fail-open shape the table's own comment demands ("ONE CLAIM, ONE ROW PER PROBE: no runner-safety capability may be decided by a HELPER EXISTING"). Arrange it by building the jail with the DENIED port ALSO allowed, through E-02's allowed-ports hook, so the ruleset really applies and really refuses nothing, and restore in a `finally` because the patch is process-global. Do NOT arrange it by patching the probe to return False, which would test the patch rather than the mechanism.
  - Depends on: E-06
  - Expected outcome: A present-but-unenforcing mechanism yields False, pinned by a row a live test reads.
  - Execution state: performed

- [x] E-09 Add a test asserting the capability is False when the reported Landlock ABI is below 4, so an older kernel cannot silently inherit a True. Drive it through E-02's parent-side ABI helper (patched to return 3, restored in `finally`) rather than by requiring an ABI-3 machine; `forced_runner_safety_verdicts` is NOT that seam, because it replaces the probe's verdict wholesale and would pass against a probe with no ABI gate at all, since none is available here and F-9 records that a real-host-only test would skip everywhere and guard nothing.
  - Depends on: E-03
  - Expected outcome: The ABI gate is pinned on every host, including this one, without a skip.
  - Execution state: performed

- [x] E-07 Re-point `tests/test_host_capability_extension.py`'s `DenyPushRemovedTests` rather than deleting it, and record why in its docstring. Its purpose (`01reg8` E-02) is to stop `supports_deny_push` being reintroduced, and that purpose SURVIVES this plan intact: this plan adds a differently-named capability precisely because it cannot prove push denial. Keep every assertion that `supports_deny_push`, `CAP_DENY_PUSH`, the three action classes, and the `deny_push` output string remain absent. Only the assertion that `aw host capabilities` prints no `REFUSED  ` needs review, and it should remain true since no action is gated. Update the docstring to name both plans, so a future reader sees the guard was honored rather than worked around.
  - Depends on: E-03
  - Expected outcome: The negative guard still fails if anyone reintroduces the `deny_push` name, and its docstring records that this Set added a narrower capability instead of evading it.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL or quoted content string, never by a bare line number (spec `ipd-structure-and-linting` Section 10.2; `IPD-C801`). Enforced throughout; this area has three stale citations of the same rule already (`:88-95`, `:109-115`, and the code-comment twin).
- A capability may be set True ONLY by code that executed a probe for it: `HostSandboxCapabilities`' docstring states "Every capability defaults to False: an UNPROBED host claims NOTHING (fail-closed)."
- Presence inference is FORBIDDEN IN WRITING, in the module docstring's `supports_commit_gateway` bullet ("Inferring support from the presence of the driver-side `git_commit_helper.offer_commit` helper is FORBIDDEN") and again in the `_DECLARED_UNENFORCED` rationale comment. E-06 pins it for the new capability.
- A probe passes only by proving a DENIAL, never a launch: the module docstring states "EVERY RUNG MUST PROVE A DENIAL, NOT A LAUNCH", with the reason that a misconfigured permissive jail "starts perfectly cleanly and enforces nothing". `_denial_checker_source` encodes it with distinct exit codes per failure shape.
- Probe failures are swallowed to False at three layers: `_run_probe` maps any `OSError`/`SubprocessError` (including `TimeoutExpired`) to nonzero, `_probe_linux_sandbox` catches any exception, and a non-Linux platform short-circuits. A new probe must join that discipline rather than raise.
- Runner-safety verdicts are deliberately NOT cached, unlike the sandbox ladder: `probe_runner_safety_capabilities`' own rationale is that "a stale memo here would be a way for one turn's verdict to outlive the state it was measured against." A capability registered in `_RUNNER_SAFETY_PROBES` inherits that, and also inherits the `forced_runner_safety_verdicts` test seam for free.
- `aw host capabilities` needs no change to show a new field: `host_cmd._capability_rows` introspects `caps.to_dict()` for bool values so that "a field added to the contract cannot silently vanish from the report".
- A test must exercise behavior, never pin code structure (AGENTS.md P16): no `inspect`/`ast`/regex reads of production source. Note `tests/test_host_capability_wiring.py` contains a pre-existing AST-based test; this plan adds no new test of that shape.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | Two-sided kernel TCP denial is provable | Research `uq4y6q` Finding 1: allowed connect `True`, denied connect `PermissionError(13)`, `RESULT: ENFORCED` at ABI 4 | The probe in E-02 is buildable and can meet the prove-a-denial standard. |
| F-2 | The existing bootstrap extends in place | Research `uq4y6q` Finding 2: one ruleset enforced both classes. `landlock_bootstrap_source` already packs `handled_access_net` as the literal `0` in `struct.pack("=QQ", ALL, 0)` | E-01 is a change to one packed value plus a rule loop, not a new mechanism or a new dependency. |
| F-3 | Net rules are port-only, address-blind | Research `uq4y6q` Finding 3: rule struct is `{allowed_access, port}`, 16 bytes, no address; two distinct hosts both connected on the allowed 443 | THE reason the capability is not named `supports_deny_push`. It proves port denial and nothing more. |
| F-4 | Denying 443 would deny the product | `oc_runipd._apply_execution_profile` wraps the worker argv that launches the coding agent, which needs the model API on 443 | The capability must not be described as a push boundary, and no action may be gated on it in this plan. |
| F-5 | A live negative test pins `supports_deny_push`'s absence | `tests/test_host_capability_extension.py` class `DenyPushRemovedTests` asserts the field, `CAP_DENY_PUSH`, the three action classes, and the `deny_push` output string are all absent | E-07 RE-POINTS rather than deletes it. Deleting a deliberate guard to make a new field fit would be the wrong move even though the new field has a different name. |
| F-6 | The three removed action classes must not come back without a consumer | `ACTION_CLASSES` is `(ACTION_READ_ONLY,)`; the comment beside `ACTION_CAPABILITY_REQUIREMENTS` warns a future reader "must not 'restore parity' by re-adding the three unused constants without a consumer" | E-03 adds NO action class and NO requirement row. The capability is reported-only. |
| F-7 | The action preflight is wired but fires for nothing | `runner_shared.execute_item_core` calls `preflight_host_capabilities`, but `RUNNER_ACTION_TO_CONTRACT_ACTION` is empty and `runner_action_contract_class` returns None for every action; the module docstring's HONEST LIMIT says "no production action requires a capability today ... so today this prevents nothing on its own" | Adding a reported capability changes no run behavior, which is the intended blast radius. A plan wanting enforcement would have to populate that mapping, which this plan deliberately does not. |
| F-8 | A forced-verdict test seam already exists | `forced_runner_safety_verdicts` context manager plus the `_FORCED_RUNNER_SAFETY` global; `probe_runner_safety_capabilities` consults it and prefixes the note with `"FORCED VERDICT (test seam): "` | Registering in `_RUNNER_SAFETY_PROBES` gives the new capability a fake/skip seam with no new test infrastructure. |
| F-9 | A real-binary-only test would skip everywhere | `tests/test_host_sandbox_profile.py`'s `BWRAP_STUB_MODES` comment records that the real binary cannot create a userns on most CI machines, so a test driving only it "would SKIP everywhere and guard nothing"; the module docstring states a skip "leaves the guarantee UNVERIFIED on that machine" and is never acceptance evidence | E-05/E-06 must include coverage that runs WITHOUT a working kernel jail (forced verdicts and the ABI gate), so the fail-closed behavior is pinned even where the real probe cannot run. The two quoted strings live in DIFFERENT places in that file and the original finding attributed both to the stub rationale; corrected at review so an executor greps the right one. |
| F-10 | THE CHILD CANNOT BIND ITS OWN ALLOWED PORT (measured at review) | `landlock_bootstrap_source` applies the ruleset and `execv`s in that order, so every allowed port is fixed before the child exists. Measured on this host: with only port `40001` allowed and `restrict_self` applied, the process bound `127.0.0.1:56659` successfully (only `CONNECT_TCP` is handled, so `bind` is unrestricted) and connecting to its OWN socket returned `[Errno 13] Permission denied`. The parent-binds design was then demonstrated to work: parent listeners on `46623`/`46745`, extended bootstrap plus checker, `rc: 0` with `denied connect refused: [Errno 13] Permission denied` | E-02 as originally authored ("the child binds a loopback listener, applies a ruleset allowing only that listener's port") COULD NOT REACH True on any host. E-02 now specifies parent-binds and E-02's Expected outcome requires True on a capable host, so the impossibility cannot pass as a fail-closed result. |
| F-11 | `PRESENCE_VS_OBSERVATION` IS DEAD DATA WITH NO CONSUMER (measured at review) | An `ast` walk of `tests/test_host_capability_extension.py` for every `Name`/`Attribute` reference to `PRESENCE_VS_OBSERVATION` returns exactly `[('name', 235)]`, its own assignment. Commit `80db6750` ("test: delete 366 tests that pinned code structure instead of behaviour") deleted `test_no_runner_safety_probe_infers_support_from_helper_presence`, the only consumer, and left the table behind; the table's own comment still claims "`_helper_exists` is asserted per row", and no symbol `_helper_exists` exists anywhere in the repository | E-06 as originally authored would have added a row to data nothing reads, and V-06 would have pasted a green line proving nothing. E-06 now restores a live consumer FIRST and adds the row second, and V-06's inversion check is what proves the consumer exists. The three surviving rows regain their guarantee as a side effect. |
| F-12 | The new capability's verdict is UNCACHED and costs a subprocess per call | `probe_runner_safety_capabilities` is deliberately not memoized ("a stale memo here would be a way for one turn's verdict to outlive the state it was measured against"), unlike `_SANDBOX_PROBE_CACHE`. Measured at review: the extended bootstrap probe costs a mean `0.047s` over five runs; warm `detect_host_capabilities('opencode')` is `0.305s`, so the projected warm cost is `0.352s`, about `1.2x` | ACCEPTABLE, and recorded so it is a measured choice rather than an unexamined one. `detect_host_capabilities` is called once per `aw host capabilities` invocation and, in a run, ONCE PER RUN: runners read the descriptor frozen in run state by `runner_shared.ensure_frozen_host_capabilities` and probe only if it is absent (corrected at the 2026-10-07 review; the earlier "once per gated action" path is not how runners reach it). A resumed run whose frozen descriptor predates this field rehydrates through `HostSandboxCapabilities.from_dict`, which keeps only known keys, so the field reads its default False there: fail-closed. The remaining multiplier is the test suite, which calls the detector directly in many places. A 47ms addition to a 305ms read-only report is not user-perceptible, so this is not the `bug`-class inefficiency AGENTS.md describes. V-03 pastes the real command so the figure is re-established rather than assumed. |

## Proposed changes (ordered, validatable)

1. Extend the bootstrap to carry optional network rules, defaulted off so every existing caller is
   byte-unchanged (E-01).
2. Add the two-sided executed probe, PARENT-BINDING both listeners, fail-closed at every layer the
   existing probes are (E-02). Parent-binding is a correctness requirement, not a style choice: F-10
   measures why the child-binds shape can never report True.
3. Add the capability, register its real probe, report it, and append the contract-field tuple entry
   in the same pass so the suite is green at the end of the item; gate nothing (E-03).
4. Amend the published-guarantees docstring to describe what it proves and what it does not (E-04).
5. Pin the probe's fail-closed behavior with tests that fail against a constant-returning probe (E-05).
6. Restore a live consumer for the `PRESENCE_VS_OBSERVATION` table, which is currently dead data
   (E-06). This precedes adding any row to it, because F-11 measures that a row added today asserts
   nothing.
7. Add the new capability's presence-versus-observation row (E-08).
8. Pin the ABI < 4 gate through the test seam (E-09).
9. Re-point the `deny_push` removal guard, preserving its purpose and recording why (E-07).

## Deferred / out of scope (with reason)

- GATING any action on the new capability, which would require populating
  `RUNNER_ACTION_TO_CONTRACT_ACTION` and re-adding an action class. Deliberately excluded: the
  capability proves port denial, and no action's safety argument rests on port denial alone while the
  443 hole (F-3, F-4) is open. Gating on it would imply a boundary that does not exist.
  - Carrier: sv9ce4
- REINTRODUCING a `RUN-NO-PUSH`-shaped finding code in spec 4.2. Backlog `oq05nc` gates this on a
  probe existing, and after this plan the probe proves PORT denial, not push denial, so the gate is
  still unmet. `run_evidence.validate_finding_table` also hard-fails on a code count other than 12.
  - Carrier-Declined: NOT WANTED and not owed. Binding a push-denial code to a port probe is exactly
    the fail-OPEN inference `run_evidence`'s retirement comment forbids ("DO NOT REINTRODUCE THE CODE
    BOUND TO A PRESENCE CHECK ... strictly worse than having no code at all"). The condition for a
    legitimate reintroduction is recorded in the spec, findable without asserting pending work.
- HOST-GRANULAR filtering (network namespace plus filtering proxy), the only mechanism that would
  close the 443 gap and make a real push-denial claim possible.
  - Carrier: sv9ce4
- WITHHOLDING remote credentials, the other half of 5.2's bullet. PARTLY built, bounded in three
  ways, and NOT "already built and shipped" as this row previously claimed (corrected at review; the
  identical overclaim was found and fixed in Order 01's own review as its PR-701, so leaving it
  standing here would have re-asserted in this plan exactly what the sibling plan was corrected for).
  The three bounds, each measured: (a) FILES ONLY, since `oc_runipd._hardened_credential_paths` makes
  `~/.ssh`, `~/.netrc`, `~/.git-credentials`, `~/.config/gh` and peers inaccessible, while
  `runner_shared.pinned_child_env` is `os.environ.copy()` and the launcher pops only four internal
  keys, so a `GH_TOKEN`/`GITHUB_TOKEN` or a forwarded `SSH_AUTH_SOCK` reaches the worker untouched and
  an environment token is a PUSH-CAPABLE credential; (b) OPT-IN AND LINUX-ONLY, since
  `_apply_execution_profile` returns `argv` unchanged unless the `hardened` profile was requested, so
  the default profile withholds nothing; (c) EXISTING PATHS ONLY, a fixed enumeration rather than a
  boundary over all credentials.
  - Carrier-Declined: Nothing is owed BY THIS PLAN, which adds no credential handling at all, and the
    bounded state is recorded in the spec by Order 01's E-03 (whose wording its review pinned to state
    all three bounds). This row exists to stop a reader of THIS plan inferring that the credential half
    is complete, which is the fail-OPEN direction the whole Set exists to refuse.
- Naming the capability `supports_deny_push`. Refused on measured grounds (F-3, F-4), not on caution.
  - Carrier-Declined: DELIBERATELY NOT WANTED. The name would assert what the mechanism cannot do,
    which is the overclaim plan `4h7tt0` retired and `01reg8` deleted.

## Scope check

- Over-scope: none. `host_sandbox_profile.py` is changed by E-01 through E-04; `tests/test_host_sandbox_profile.py`
  by E-03's one-line `CONTRACT_FIELDS` append and E-05; `tests/test_host_capability_extension.py` by
  E-06, E-07, E-08 and E-09; the spec by the capability's appearance in 5.2's descriptor narrative, which
  is a one-paragraph addition recording that the first probed answer now exists; `CHANGELOG.md` by the
  unreleased entry the user-visible report row warrants.
- Under-scope: none. `host_cmd.py` is deliberately NOT in scope and needs no change, because
  `_capability_rows` introspects `to_dict()` for bools (F-7's sibling finding), so the new row appears
  automatically; V-03 verifies that by running the real command rather than assuming it. NOTE the new
  row also appears in the `aw host capabilities --json` payload for free, and no shipped test pins the
  capability-row COUNT (measured at review: `test_the_json_payload_carries_the_full_contract_and_action_verdicts`
  asserts `len(data["action_classes"]) == 1` and `len(host["actions"]) == 1`, both action counts, and
  `test_the_capability_rows_are_derived_by_introspection` asserts membership rather than length), so
  adding a field breaks no count assertion. This is why `host_cmd.py` and its tests need no edit; it is
  stated because a count assertion is exactly what would have made this an under-scope miss.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. This plan changes a
  shipped dataclass and two test files, so the suite is the primary gate.
- The new probe tests must pass ON THIS HOST, and a SKIP is not acceptance evidence
  (`tests/test_host_sandbox_profile.py`'s stated policy: "a skip leaves the guarantee UNVERIFIED on
  that machine"). If the executing host reports ABI < 4, the real-denial test legitimately skips and
  the ABI-gate and forced-verdict tests MUST still run and pass; say so explicitly in the evidence
  rather than pasting a green line that hides a skip.
- `aw host capabilities opencode` must be run and its actual output pasted, showing the new row and
  its probe note.
- `aw ipd lint` conforming; `aw check` reporting no new violations.
- `aw sanitize --agent` exiting zero: probe notes and pasted command output can carry host paths.

## Spec / documentation sync

- Spec `25kzda` is AMENDED (declared in `Scope-Paths`) with one paragraph in 5.2 recording that the
  network requirement now has its first PROBED answer, what that answer proves (port denial, two-sided,
  per host), and what it still does not prove (push denial, because the mechanism is address-blind).
  WHY this belongs in the same change: 5.2 requires descriptor entries be "backed by positive and
  fail-closed probe evidence" and states "`supported` without current evidence is not sufficient", so
  adding the first such entry for this requirement changes what the contract can claim, and leaving
  the spec silent would leave the next reader unable to tell a probed row from a declared one.
- `host_sandbox_profile`'s module docstring is the published-guarantees contract and is amended by
  E-04, including the field-count prose it currently carries.
- CHANGELOG: an entry IS warranted here, since `aw host capabilities` gains a user-visible row, and
  `CHANGELOG.md` is now DECLARED in `Scope-Paths` (added at review). The previous wording said the
  entry was warranted but left the path undeclared "as a separate concern" and offered to add it "at
  review time"; that is a contradiction the finalize scope gate would have caught rather than
  tolerated. `ipd_lifecycle._is_implicitly_allowed` grants only `.aw/records/plans/**`,
  `.aw/records/plans/INDEX.md` and `.aw/records/**/index.md` (measured at review via
  `ipd_schema.scope_paths_implicit_allowances()`), so `CHANGELOG.md` is NOT implicitly allowed and an
  undeclared edit to it would have demanded a `--scope-reason` at finalize for work the plan already
  knew it was going to do. Write the entry in user-facing prose with NO em or en dashes, per the
  execution contract.

## Open questions

### OQ-01: Is `supports_deny_tcp_port` the right name, or should it be `supports_deny_outbound_tcp_port`?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED AT REVIEW: keep `supports_deny_tcp_port`, the shorter
  name, and carry the direction in the `probe_notes` entry rather than in the field name. The
  ambiguity the question raises is REAL and was confirmed by measurement rather than from
  documentation: at ABI 4 this kernel accepts a ruleset handling `LANDLOCK_ACCESS_NET_BIND_TCP`
  (`1 << 0`) just as readily as one handling `LANDLOCK_ACCESS_NET_CONNECT_TCP` (`1 << 1`), both
  returning a valid ruleset fd, so the two rights genuinely are separate and a bare "tcp_port" does
  not say which one was proven. What decides it is that the field name is not the only place the
  claim is published: `host_cmd._capability_rows` emits the `probe_notes` entry directly beneath
  every row (verified by running `aw host capabilities opencode`, whose output renders each verdict
  followed by its own `why:` line), so the direction is read at the same moment as the verdict and
  never separately. Given that, the shorter name costs nothing a reader can be misled by, while the
  longer one spends 8 characters on information already present at the point of use. This is a
  REVERSIBLE decision: renaming a dataclass field before anything gates on it is a mechanical change,
  and nothing outside this repository consumes the name. A maintainer who prefers
  `supports_deny_outbound_tcp_port` should say so, and `wcbpqf` remains available if they want it
  recorded as a standing decision. E-02's probe note MUST state the direction explicitly; that is now
  a requirement of this resolution and not merely a nicety.

### OQ-02: Should this capability be registered in RUNNER_SAFETY_CAPABILITIES, or is it a sandbox-ladder capability like supports_os_sandbox?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: register it in
  `RUNNER_SAFETY_CAPABILITIES`. Two properties of that group decide it. FIRST, membership is what
  wires a capability into `_RUNNER_SAFETY_PROBES`, and that group's verdicts are deliberately NOT
  cached ("a stale memo here would be a way for one turn's verdict to outlive the state it was
  measured against"), which is the correct semantics for a network verdict that can change with host
  configuration between turns. The sandbox ladder, by contrast, memoizes in `_SANDBOX_PROBE_CACHE`.
  SECOND, membership grants the `forced_runner_safety_verdicts` test seam for free, which F-9 shows
  this plan needs, since a real jail is unavailable on many hosts. The ladder is also the wrong home
  on its own terms: `_SANDBOX_LADDER` rungs are ALTERNATIVE mechanisms for one filesystem-partition
  question, chosen strongest-first, whereas this is an independent question with its own answer.
  THE COST OF NOT CACHING WAS MEASURED AT REVIEW rather than left as an unexamined consequence of the
  FIRST argument above, since choosing the uncached group means paying a subprocess on every call: the
  extended bootstrap probe costs a mean 0.047s over five runs, against a warm
  `detect_host_capabilities('opencode')` of 0.305s, so the projected warm total is 0.352s (about 1.2x).
  `detect_host_capabilities` runs once per `aw host capabilities` invocation and once per RUN (the
  descriptor is frozen in run state by `runner_shared.ensure_frozen_host_capabilities`; corrected at
  the 2026-10-07 review, see F-12), never per queue item, so this is not a user-perceptible regression and not the
  `bug`-class inefficiency AGENTS.md describes. Recorded in F-12 so a later reader can dispute the
  number rather than the judgement. NOTE ALSO that membership in `RUNNER_SAFETY_CAPABILITIES` gates
  nothing by itself: `check_action_capabilities` reads `ACTION_CAPABILITY_REQUIREMENTS`, whose only row
  (`read_only`) has `required=()`, so registering here cannot make any action start refusing.

### OQ-03: Should the probe allow the model API port so the capability could eventually be enabled in production, rather than proving denial on an arbitrary port?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: no, and the distinction matters. The probe's job is to
  establish whether THE KERNEL ENFORCES a port partition on this host, which is a question about the
  host and not about our port policy. Proving it with a loopback listener is strictly better evidence
  because it is hermetic, needs no external network, and gives a genuine two-sided result in CI. What
  ports a production hardened profile would allow is a POLICY decision that belongs with the work that
  actually applies network rules to a worker, and that work is carried by BACKLOG `sv9ce4` ("Build
  host-granular outbound network filtering (netns plus filtering proxy), the only mechanism that can
  deny a git push without also denying the model API", verified `open` at review), because applying a
  policy requires solving the 443 problem first (F-3, F-4). CORRECTED AT REVIEW: this rationale
  previously named `wzhe4n`, which is Order 03 of this same Set, a records-and-verification plan whose
  own Scope says "no product code" and which therefore cannot carry a network-policy deliverable. Every
  other deferral row in this plan already names `sv9ce4`, so the one that named a sibling plan was the
  outlier. Conflating policy with the probe would put a policy choice inside a capability probe, where
  it would be untestable and would quietly change what the capability means.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: A pasted assertion that the no-port call is byte-identical to today's output, e.g. comparing `landlock_bootstrap_source(w, r, argv)` before and after via a captured digest, plus the pasted `python3 -m pytest tests/test_host_sandbox_profile.py` result showing `LandlockBootstrapTests` still passes. Also paste the generated source for a WITH-ports call showing the connect-TCP bit in the ruleset attr and one net-port rule per requested port, and showing the ABI >= 4 guard around the network rules.
  - Observed evidence:
    No-port call digest comparison:
    ```
    HEAD orig_digest: 7a275449a1804db0437775b9da0098b996e3bc82139790a7956ca788d8a32321
    Current curr_digest: 7a275449a1804db0437775b9da0098b996e3bc82139790a7956ca788d8a32321
    Identical: True
    ```
    Pytest result:
    ```
    $ python3 -m pytest tests/test_host_sandbox_profile.py -k LandlockBootstrapTests
    .                                                                        [100%]
    1 passed in 7.53s
    ```
    Generated source snippet for call with `allowed_tcp_ports=[8080]`:
    ```python
    if abi >= 4:
        NET = 1 << 1
    else:
        NET = 0

    attr = struct.pack("=QQ", ALL, NET)
    buf = ctypes.create_string_buffer(attr, len(attr))
    fd = libc.syscall(LL_CREATE, ctypes.byref(buf), ctypes.c_size_t(len(attr)), ctypes.c_uint32(0))
    if fd < 0:
        sys.stderr.write("landlock_create_ruleset failed errno=%d\n" % ctypes.get_errno())
        raise SystemExit(125)

    if abi >= 4:
        for port in [8080]:
            rule = struct.pack("=QQ", 1 << 1, port)
            rb = ctypes.create_string_buffer(rule, len(rule))
            if libc.syscall(LL_ADD_RULE, ctypes.c_int(fd), ctypes.c_uint32(2),
                            ctypes.byref(rb), ctypes.c_uint32(0)) != 0:
                sys.stderr.write("landlock add_rule net_port failed for port %d errno=%d\n"
                                 % (port, ctypes.get_errno()))
                raise SystemExit(125)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: The probe's own returned `(bool, note)` for three arrangements, pasted: the real host (whatever it reports), a forced ABI < 4 condition, and an induced probe exception. The first must show a note that states the evidence rather than a bare False. Additionally show the probe distinguishes the two failure shapes by exit code: a jail that denies the ALLOWED connect must not report True, and a jail that permits the DENIED connect must report False with a note saying it was not enforced. A single True with no failure-shape evidence FAILS this item, since that is the launch-only criterion the module docstring forbids.
  - ON A HOST REPORTING ABI >= 4, THE REAL-HOST ARRANGEMENT MUST RETURN True, and a False there FAILS this item rather than being recorded as the measurement. This is the check that catches F-10: the child-binds design returns a perfectly fail-closed False on a fully capable host, so "the probe reported False and False is safe" is exactly the answer that would hide the defect. Paste the host's own reported ABI beside the verdict so the two can be read together. If and only if the executing host reports ABI < 4 is a False legitimate, and then say so explicitly and state that the two-sided denial is consequently UNVERIFIED on this machine.
  - Observed evidence:
    Executing host Landlock ABI: 4
    Real host probe result:
    ```
    (True, 'outbound TCP connect denial proven by executed two-sided probe (LANDLOCK_ACCESS_NET_CONNECT_TCP); limit: per-port only with no destination address filtering, so port 443 git remote push cannot be distinguished from model API traffic')
    ```
    Forced ABI < 4 condition:
    ```
    (False, 'landlock network rules require ABI >= 4; kernel reported ABI 3')
    ```
    Induced probe exception:
    ```
    (False, 'deny_tcp_port probe failed: RuntimeError: simulated boom')
    ```
    Failure shape: allowed connect denied (rc=3):
    ```
    (False, 'landlock network jail too restrictive: allowed connect was denied (rc=3): allowed connect was DENIED: PermissionError')
    ```
    Failure shape: denied connect succeeded (rc=4):
    ```
    (False, 'landlock network jail did not enforce: denied connect succeeded (rc=4): denied connect SUCCEEDED - not enforced')
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Actual pasted output of `aw host capabilities opencode` showing the new row and its probe note, plus `python3 -c` output printing `CAP_DENY_TCP_PORT in hsp.__all__`, `hsp.RUNNER_SAFETY_CAPABILITIES`, `hsp._RUNNER_SAFETY_PROBES[hsp.CAP_DENY_TCP_PORT] is not None` (proving it is PROBED, not the declared-not-probed `None` sentinel), and `hsp.ACTION_CLASSES` still equal to `(hsp.ACTION_READ_ONLY,)`. The last is what proves no action was gated.
  - Observed evidence:
    Output of `aw host capabilities opencode`:
    ```
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
      yes  supports_deny_tcp_port (runner-safety)
           why: outbound TCP connect denial proven by executed two-sided probe (LANDLOCK_ACCESS_NET_CONNECT_TCP); limit: per-port only with no destination address filtering, so port 443 git remote push cannot be distinguished from model API traffic
      actions:
        ALLOWED  read_only
                 not representable by this contract: complete_diff_capture
        ALLOWED  execute
                 not representable by this contract: isolated_worktree, path_policy, argv_capture, timeout_cancel, hook_preserving_commit, complete_diff_capture

    1 host(s) reported; 0 (host, action) pair(s) refused
    ```
    Symbol export, registration, probe wiring, and action class verification:
    ```
    "CAP_DENY_TCP_PORT" in hsp.__all__: True
    hsp.CAP_DENY_TCP_PORT: 'supports_deny_tcp_port'
    hsp.RUNNER_SAFETY_CAPABILITIES: ('supports_commit_gateway', 'supports_fresh_verifier_session', 'supports_deny_tcp_port')
    hsp._RUNNER_SAFETY_PROBES[hsp.CAP_DENY_TCP_PORT] is not None: True
    hsp.ACTION_CLASSES: ('read_only', 'execute')
    hsp.ACTION_CAPABILITY_REQUIREMENTS: {'read_only': ActionRequirement(action='read_only', required=(), ...), 'execute': ActionRequirement(action='execute', required=('supports_fresh_verifier_session',), ...)}
    ```
    Note on action classes: `pi3bk8` added NO action class and added NO requirement to `ACTION_CAPABILITY_REQUIREMENTS`. `ACTION_EXECUTE` is present on `main` from predecessor plan `y9m1ya` (requiring `supports_fresh_verifier_session`); `supports_deny_tcp_port` gates zero actions.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `git diff` of the docstring showing the new bullet, the corrected count prose (no longer claiming "Two fields"), and an explicit statement of the port-granularity limit and of the gates-nothing limit. A diff that adds the bullet without the limit FAILS, since an unqualified bullet in the published-guarantees contract is the overclaim this Set exists to avoid.
  - Observed evidence:
    `git diff` of module docstring in `agent_workflows/host_sandbox_profile.py`:
    ```diff
    @@ -107,7 +107,7 @@ RUNNER-SAFETY CAPABILITIES AND THE ACTION PREFLIGHT (mjx7ne, spec 25kzda 5.2)

     The contract above answers what the host can do to CONFINE a worker. It said nothing about
     the runner-safety guarantees a lifecycle ACTION depends on, and nothing compared what an
    -action NEEDS against what a host PROVED. Two fields and a preflight close that:
    +action NEEDS against what a host PROVED. Runner-safety fields and a preflight close that:

       * `supports_fresh_verifier_session` - PROBED by attempt. The probe runs the real
         fresh-verifier contract twice and requires BOTH that distinct identities finalize AND
    @@ -131,6 +131,13 @@ action NEEDS against what a host PROVED. Two fields and a preflight close that:
         a canonical structured tool event in that host's wire schema (producing a rendered line
         containing the tool name while ignoring a well-formed non-tool event).
         Platform-independent.
    +  * `supports_deny_tcp_port` - PROBED by attempt and two-sided (pi3bk8). The probe
    +    constructs a Landlock ruleset handling outbound connect-TCP with only an allowed
    +    loopback port permitted, requires the connect to that port to succeed, and requires
    +    a connect to an unallowed port to be refused by the kernel with EACCES (errno 13).
    +    LIMIT: port-granularity only with no destination address filtering, so it cannot
    +    separate git remote push from model API traffic on TCP 443, and it gates no action
    +    today.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted output of `python3 -m pytest tests/test_host_sandbox_profile.py` showing `test_every_contract_field_exists_and_defaults_false` and `test_to_dict_snapshots_the_contract` passing WITH the new field included (the `CONTRACT_FIELDS` diff itself is V-03's, since the append moved to E-03), plus the pasted results of the two tests this item adds: the raising-probe test and the direct `_probe_deny_tcp_port` test. If any SKIPPED, paste the skip reason and state which guarantee is consequently unverified on this host.
  - PROVE THE PROBE TEST IS NOT VACUOUS. Show that the direct-probe test would FAIL against a probe returning a constant: temporarily replace `_probe_deny_tcp_port` with `lambda: (True, "constant")`, paste the FAILURE, then revert and paste the restored pass. A test that passes against a constant-returning probe is the fail-open shape this plan's whole test discipline exists to reject, and it is exactly what the original "verdict equals a forced re-run of the probe" wording would have produced.
  - Observed evidence:
    Passing pytest run:
    ```
    $ python3 -m pytest tests/test_host_sandbox_profile.py -k "test_every_contract_field_exists_and_defaults_false or test_to_dict_snapshots_the_contract or DenyTcpPortProbeTests"
    ....                                                                     [100%]
    4 passed in 7.25s
    ```
    Non-vacuity proof against constant probe:
    ```
    test_probe_deny_tcp_port_directly (tests.test_host_sandbox_profile.DenyTcpPortProbeTests.test_probe_deny_tcp_port_directly) ... FAIL

    ======================================================================
    FAIL: test_probe_deny_tcp_port_directly (tests.test_host_sandbox_profile.DenyTcpPortProbeTests.test_probe_deny_tcp_port_directly)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "tests/test_host_sandbox_profile.py", line 1239, in test_probe_deny_tcp_port_directly
        self.assertIn("outbound TCP connect denial proven", note)
    AssertionError: 'outbound TCP connect denial proven' not found in 'constant'

    ----------------------------------------------------------------------
    Ran 1 test in 0.021s

    FAILED (failures=1)
    ```
    Restored pass:
    ```
    test_probe_deny_tcp_port_directly ... ok
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PROVE THE CONSUMER EXISTS, which is the whole deliverable. Paste an `ast`-based count of references to `PRESENCE_VS_OBSERVATION` in `tests/test_host_capability_extension.py` showing MORE THAN ONE (the assignment plus the new consumer); a count of exactly 1 means the table is still dead and this item FAILS regardless of how green the suite is. Paste the new test's result showing the three EXISTING rows passing. To prove it is not vacuous, temporarily invert one probe so a negative row's verdict flips, paste the resulting FAILURE, then revert and paste the restored pass; a test that cannot be made to fail by inverting a probe is not consuming the table.
  - Also state that the restored test reads no production SOURCE (no `inspect`, no `ast` over `agent_workflows/`, no substring search of module text), since the deleted consumer was removed for being a structure pin and restoring that shape would re-create the defect commit `80db6750` removed.
  - Observed evidence:
    AST-based count of `PRESENCE_VS_OBSERVATION` references (Name and Attribute):
    ```
    AST references (Name/Attribute): [('name', 254), ('attr', 308)]
    Count: 2
    ```
    Test result for existing 3 rows:
    ```
    test_presence_vs_observation_table (tests.test_host_capability_extension.RunnerSafetyProbeTests.test_presence_vs_observation_table)
    E-06: consumer for PRESENCE_VS_OBSERVATION table. ... ok
    Ran 1 test in 0.937s
    OK
    ```
    Inverted probe failure demonstration (inverting fresh-verifier probe to True):
    ```
    ======================================================================
    FAIL: test_presence_vs_observation_table (tests.test_host_capability_extension.RunnerSafetyProbeTests.test_presence_vs_observation_table) (case='fresh-verifier separation, with the contract present but REFUSING NOTHING', capability='supports_fresh_verifier_session')
    E-06: consumer for PRESENCE_VS_OBSERVATION table.
    ----------------------------------------------------------------------
    AssertionError: True is not False : row failed: fresh-verifier separation, with the contract present but REFUSING NOTHING; expected False but got True; why: THE ROW THAT GENERALIZES THE RULE BEYOND AN ABSENT ENFORCEMENT. Here the enforcement mechanism really does exist and really does run, so `the symbol imports` is at its most tempting - and a contract that ACCEPTS a reused session identity separates execution from verification not at all, while a caller believes the two were independent. The observed REFUSAL is the evidence, never the symbol
    ----------------------------------------------------------------------
    Ran 1 test in 0.841s
    FAILED (failures=1)
    ```
    The restored test drives `probe_runner_safety_capabilities` under context managers and asserts returned boolean verdicts; it reads zero production source code and performs no AST/inspect analysis.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: Pasted result of the table-consuming test showing all FOUR rows passing, the new row included. Quote the new row's `arrange` and state, in one sentence, HOW it makes the mechanism present and reachable while nothing is refused; an arrangement that patches the probe's return value FAILS this item, because it tests the patch. To prove the row is load-bearing, temporarily make the probe return True unconditionally, paste the FAILURE naming this row, then revert and paste the restored pass.
  - Observed evidence:
    All 4 rows passing:
    ```
    test_presence_vs_observation_table (tests.test_host_capability_extension.RunnerSafetyProbeTests.test_presence_vs_observation_table)
    E-06: consumer for PRESENCE_VS_OBSERVATION table. ... ok
    Ran 1 test in 0.853s
    OK
    ```
    Row 4 `arrange` quote:
    ```python
    @contextlib.contextmanager
    def _deny_tcp_port_both_ports_allowed():
        orig_hook = hsp._deny_tcp_probe_allowed_ports
        hsp._deny_tcp_probe_allowed_ports = lambda allowed, denied: (allowed, denied)
        try:
            yield
        finally:
            hsp._deny_tcp_probe_allowed_ports = orig_hook
    ```
    Mechanism explanation: The hook patches `_deny_tcp_probe_allowed_ports` so that the Landlock ruleset adds `LANDLOCK_RULE_NET_PORT` rules for both the allowed and denied ports, applying a valid jail where neither port connection is refused by the kernel, thereby proving that mechanism presence without observed kernel connect refusal correctly reports False.
    Load-bearing failure demonstration (probe returning True unconditionally):
    ```
    ======================================================================
    FAIL: test_presence_vs_observation_table (tests.test_host_capability_extension.RunnerSafetyProbeTests.test_presence_vs_observation_table) (case='deny-tcp-port, with landlock present but the denied port ALSO allowed in ruleset', capability='supports_deny_tcp_port')
    E-06: consumer for PRESENCE_VS_OBSERVATION table.
    ----------------------------------------------------------------------
    AssertionError: True is not False : row failed: deny-tcp-port, with landlock present but the denied port ALSO allowed in ruleset; expected False but got True; why: The jail mechanism is present and ruleset is applied, but because both ports are allowed, no kernel connect denial is observed. Inferring support from mechanism presence without observed refusal would fail open
    ----------------------------------------------------------------------
    Ran 1 test in 0.010s
    FAILED (failures=1)
    ```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: Pasted result of the ABI-gate test PASSING on this host (not skipped), plus the reported Landlock ABI of the executing host so a reader can see the test exercised the below-4 branch through the seam rather than because the host happened to be old. PROVE IT IS LOAD-BEARING: temporarily delete the parent-side ABI check from the probe body, paste the ABI-gate test FAILING, revert and paste the pass. A SKIP fails this item: F-9 records that a skip leaves the guarantee unverified, and the gate this test covers is precisely the one an older kernel would silently pass.
  - Observed evidence:
    Executing host Landlock ABI: 4
    Passing ABI-gate test:
    ```
    test_deny_tcp_port_abi_below_4_returns_false (tests.test_host_capability_extension.RunnerSafetyProbeTests.test_deny_tcp_port_abi_below_4_returns_false)
    E-09: landlock ABI < 4 must report False with an explanatory note. ... ok
    Ran 1 test in 0.006s
    OK
    ```
    Load-bearing failure demonstration (bypassing ABI gate):
    ```
    ======================================================================
    FAIL: test_deny_tcp_port_abi_below_4_returns_false (tests.test_host_capability_extension.RunnerSafetyProbeTests.test_deny_tcp_port_abi_below_4_returns_false)
    E-09: landlock ABI < 4 must report False with an explanatory note.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "tests/test_host_capability_extension.py", line 341, in test_deny_tcp_port_abi_below_4_returns_false
        self.assertFalse(ok)
    AssertionError: True is not false
    ----------------------------------------------------------------------
    Ran 1 test in 0.002s
    FAILED (failures=1)
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: `git diff` of `DenyPushRemovedTests` showing every `supports_deny_push`/`CAP_DENY_PUSH`/action-class/`deny_push`-string assertion RETAINED and only the docstring updated, plus the pasted test result showing it passes. Also paste `aw host capabilities opencode | grep -c deny_push` returning 0, which is the behavioral proof that the new capability did not smuggle the forbidden name into the report.
  - USE `grep -c 'REFUSED  '` (TWO TRAILING SPACES) FOR THE REFUSED CHECK, NOT A BARE `REFUSED`, and state the number. Measured at review on the current tree: a bare `grep -c REFUSED` on `aw host capabilities opencode` returns **1**, because the fresh-verifier probe note contains the sentence "a reused-identity run was REFUSED"; the two-space form returns **0**, and it is the two-space form `DenyPushRemovedTests` actually asserts (`self.assertNotIn("REFUSED  ", out)`). An executor who greps the bare word will see a hit, conclude the test's premise broke, and either "fix" a passing guard or report a false regression.
  - Observed evidence:
    `git diff` of `DenyPushRemovedTests`:
    ```diff
     class DenyPushRemovedTests(unittest.TestCase):
    -    """01reg8 E-02: verify supports_deny_push and the three unenforced action verdicts are gone."""
    +    """01reg8 E-02 / pi3bk8 E-07: verify supports_deny_push and unenforced action verdicts remain gone.
    +
    +    Plan pi3bk8 added the narrower capability supports_deny_tcp_port because Landlock proves TCP port
    +    denial and cannot prove remote push denial. This guard verifies that supports_deny_push and
    +    CAP_DENY_PUSH remain absent and were not reintroduced or worked around.
    +    """

         def test_supports_deny_push_and_unenforced_action_verdicts_removed(self):
    ```
    Test execution result:
    ```
    $ python3 -m pytest tests/test_host_capability_extension.py -k DenyPushRemovedTests
    .                                                                        [100%]
    1 passed in 7.88s
    ```
    Grep assertions:
    ```
    $ python3 -m agent_workflows host capabilities opencode | grep -c deny_push
    0
    $ python3 -m agent_workflows host capabilities opencode | grep -c 'REFUSED  '
    0
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHETHER THIS PLAN SHOULD EXECUTE AT ALL IS A MAINTAINER DECISION RECORDED ELSEWHERE. Orchestrator `l4vw9o` OQ-01 ("Should this Set ship the port-denial capability at all, or record the measurement and stop?") is `open`, `Blocking: no`, owner maintainer, carrier `wcbpqf`. Approving this plan IS answering "ship it"; a maintainer who prefers "record and stop" should decline this plan (and `wzhe4n`, which depends on it) instead. Recorded here so the approver of THIS plan sees the question at the point of approval rather than only on the parent.

The whole design of this plan is to deliver the smallest thing that is HONESTLY TRUE. The measured
mechanism proves port denial, so the capability is named for port denial, reports port denial, and
gates nothing. A reviewer should specifically check that no artifact this plan touches can be read as
claiming push denial, because that overclaim is the exact defect plan `4h7tt0` retired and plan
`01reg8` deleted, and the cheapest way to recreate it is to build a working probe and then describe it
generously.

TWO THINGS A REVIEWER SHOULD PUSH HARDEST ON, both found by measurement at this review and both of a
kind the suite cannot catch. FIRST, THE PROBE MUST BE ABLE TO SAY YES. A probe that can only ever
report False is fail-closed and therefore looks safe, which is exactly why it survives review: the
originally authored child-binds design could not reach True on ANY host (F-10), and its False would
have been pasted as "the measurement". So the acceptance bar in E-02 and V-02 is a True on a capable
host, not merely a defensible False. SECOND, A TEST MUST BE ABLE TO SAY NO. The table this plan
originally proposed extending has had no consumer since commit `80db6750` (F-11), so a fourth row plus
a green suite line would have been evidence of nothing. Both defects share one shape: an artifact that
cannot produce the answer that would reveal a problem. V-02, V-05, V-06 and V-08 each now demand a
deliberately induced FAILURE for that reason.

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`,
never `git add -A`, and never push. This is a SHARED CHECKOUT: verify the staged set with
`git diff --cached --name-only` before committing, unstage anything that is not yours with
`git restore --staged <path>`, and re-verify after any failed raw commit attempt. Run the suite BARE as
`python3 -m pytest` and PASTE ITS ACTUAL SUMMARY LINE; a summary you did not produce is not evidence,
and the same hard-MUST governs every pasted probe output and every induced-failure paste the `V-*` items
demand. Paste skips explicitly rather than letting a green line hide one.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). The five
`- Scope-Paths:` entries are the whole surface. THREE NEGATIVE CONSTRAINTS CARRY REAL WEIGHT. FIRST, do
NOT add an action class or an `ACTION_CAPABILITY_REQUIREMENTS` row: `ACTION_CLASSES` must remain
`(ACTION_READ_ONLY,)`, F-6 records the in-code warning against "restoring parity" without a consumer,
and V-03 fails otherwise. SECOND, do NOT reintroduce the `deny_push` NAME in any form, nor weaken any
assertion in `DenyPushRemovedTests`: E-07 re-points that guard and V-07 proves every assertion survived.
THIRD, do NOT add or remove a `run_evidence.RUN_FINDING_CODES` entry: `validate_finding_table` hard-fails
on a count other than 12, and the gate for a `RUN-NO-PUSH`-shaped code is deliberately unmet (see the
Deferred section). An out-of-scope edit that turns out to be necessary is to be MADE and then JUSTIFIED
to `aw ipd finalize` with a `--scope-reason` per path, and a declared-but-unmodified path needs a
`--scope-ack`; neither is a reason to stop. `CHANGELOG.md` is declared, so write the entry rather than
acking it.

LIFECYCLE TRANSITION. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete observed evidence.
Reaching `executed/` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` /
`aw agy run` the RUNNER owns the terminal transition and finalize, so do NOT invoke `aw ipd finalize`
yourself in a runner-driven execution; a HAND execution invokes it
(`aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`). Never hand-edit
`- Status:` and never hand-roll a `git mv` into `executed/`, which would skip the pre-transition
checkpoint. This plan must NOT set backlog `oq05nc` `done` or `graduated` by hand (it read `open` at the 2026-10-07 review, reopened by gradcover on 2026-10-06; graduation is the graduating run's act, and `runner_shared.evaluate_backlog_close` closes it `done` only once every `From-Backlog: oq05nc` carrier has executed).
