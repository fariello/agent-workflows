# Review findings: plan nxh5s4

- Subject-Id: nxh5s4
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `2e2225ee8` in an isolated review lane, non-interactively. The plan was committed and
byte-identical to the lane input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent`
was clean before semantic review and `--phase review-finalize` clean after revision.

Re-verified (stdin probes, no file written, no production or test edit):
- `host_sandbox_profile`: `_run_probe`, `_denial_checker_source` (exit 0/3/4), `_probe_landlock`, `_PROBE_TIMEOUT_SECONDS = 20`,
  `CERTIFIED_PLATFORM = "linux"`, `RUNNER_SAFETY_CAPABILITIES`, `_RUNNER_SAFETY_PROBES`, `forced_runner_safety_verdicts`,
  uncached `probe_runner_safety_capabilities`, `ACTION_CLASSES = (ACTION_READ_ONLY,)`.
- `detect_host_capabilities` runs the runner-safety prober under `plat == running_platform` BEFORE the `CERTIFIED_PLATFORM` gate.
- `oc_runipd._apply_execution_profile` calls `detect_host_capabilities("opencode")` unconditionally per dispatch.
- `host_cmd._capability_rows` introspects `to_dict()` bools and renders `probe_notes`.
- `tests/test_host_capability_extension.py` `test_new_contract_fields_and_defaults` imports `CONTRACT_FIELDS`;
  `PRESENCE_VS_OBSERVATION` has no reader (only its assignment); its fresh-verifier rows pair negative with positive.
- `DenyPushRemovedTests` asserts `ACTION_CLASSES` and requirement keys unchanged; unaffected by this plan.
- Probe shape through `_run_probe`: `-Urn` rc 0 `Network is unreachable`, parent got `b'HELLO'`, 0.045s; `-Ur` rc 4 `denied REACHED`;
  abstract AF_UNIX across netns `ConnectionRefusedError: [Errno 111]`.
- `pi3bk8` is `approved`, `Item-Dependencies: executed:x2dwu5`, its E-06 writes the same consumer.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | E. Testing (reachability) | E-04/E-05/V-01 demand "namespace cannot be created" and "denied side reachable" arrangements; plan named no seam | The runtime demonstrations V-01, V-04 and V-05 demand had no named code path producing them, and E-05 forbids patching the return value, so an executor had to invent architecture or fake the arrangement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires a module-level `_EGRESS_PROBE_NS_ARGV` launcher seam; demonstrated `("unshare","-Ur")` yields rc 4 not-enforced and a missing binary fails closed (F-9). E-04, E-05, V-01 use it. |
| PR-002 | HIGH | IN-SCOPE | D. Anti-regression (vacuity) | E-04 direct-probe test; V-04 checks only constant True | A test of a probe whose value is host-dependent either pins False (passes a constant-False probe, the exact `pi3bk8` F-10 failure) or pins True (fails on restricted CI). V-04 proved vacuity in one direction only. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Expected value decided by EXECUTING `unshare -Urn true` in the test; V-04 requires failures under both constant True and constant False. |
| PR-003 | MEDIUM | UNDER-SCOPE | D. Invariants | `PRESENCE_VS_OBSERVATION` fresh-verifier positive row ("the anti-vacuity half of the whole table") | E-05 added only a negative row, so the table would accept a constant-False egress prober. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05/V-05 add an `_unarranged` positive row with an executed-capability expectation and specify the witness (`unshare` executable). |
| PR-004 | MEDIUM | IN-SCOPE | E. Evidence | F-5 / OQ-02 "never per queue item"; `oc_runipd._apply_execution_profile` calls `detect_host_capabilities("opencode")` before checking the profile | False factual claim about where the uncached probe cost lands. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in F-5 and OQ-02; re-measured 0.045s per dispatch, still acceptable beside a multi-minute turn. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness | `detect_host_capabilities`: runner-safety block under `plat == running_platform` precedes the `CERTIFIED_PLATFORM` return | "honor the CERTIFIED_PLATFORM gate" was ambiguous: the existing gate does not cover runner-safety probes, so on darwin the probe runs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 requires the probe to check the platform itself and return False with a note. |
| PR-006 | MEDIUM | IN-SCOPE | A. Correctness | review probe: abstract AF_UNIX `ConnectionRefusedError: [Errno 111]`; E-01 trusted child exit code only | An abstract socket silently fails the allowed side (permanent False); trusting only the child's rc lets the allowed side go unobserved by the parent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 mandates a short filesystem-path socket and parent-observed receipt; demonstrated a blocking `_run_probe` then `accept` works. |
| PR-007 | LOW | IN-SCOPE | C. Coordination | `pi3bk8` `approved`, `Item-Dependencies: executed:x2dwu5`, its E-06 writes the same consumer | Two plans may each write the `PRESENCE_VS_OBSERVATION` consumer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05/V-05 require reuse if present, else write one reusable consumer and record it. |
| PR-008 | LOW | IN-SCOPE | G. Execution contract | gate lacked out-of-scope handling and scratch cleanup; E-03 implied an edit to `detect_host_capabilities` | Minor executability gaps. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate adds `--scope-reason`/`--scope-ack` and clean-tree proof; E-03 states verdicts flow with no `detect_host_capabilities` edit. OQ-01/02 owners set to plan author. |

### Open questions carried

- OQ-03 (name `supports_egress_filtering` vs `supports_network_namespace`): non-blocking, maintainer-owned, carried by
  backlog `wcbpqf`. Left open: a public-contract naming decision belongs to the maintainer and is shared with sibling Set plans.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How do tests arrange mechanism outcomes without patching the probe's return? | Module-level launcher-argv seam `_EGRESS_PROBE_NS_ARGV` | Patch `subprocess.run` (brittle, couples to `_run_probe` internals); patch return value (forbidden by E-05) | review probe `-Ur` rc 4 not-enforced | yes |
| D-2 | What is the direct-probe test's expected value on an unknown host? | Decided by executing `unshare -Urn true` in the test | `shutil.which("unshare")` (presence inference, forbidden); hard-coded True (red on restricted CI) | module docstring presence-inference ban; F-4 host variance | yes |
| D-3 | Should the probe enforce the platform gate itself? | Yes | Rely on `detect_host_capabilities` gate (does not cover runner-safety probes) | `detect_host_capabilities` block order | yes |

## Round 2

Re-review on 2026-10-07 in isolated review lane at HEAD `e9de18a08` by opencode/its_direct/pt3-claude-opus-5.5-1m-us, after
gradcover `52opph` demoted the plan and it returned to `to-review` with the Set-level bare-suite sweep assigned to
`wn956n` E-05/V-05. Plan byte-identical to lane input and committed, so no pre-review snapshot. `aw ipd lint --phase
author --agent`: `clean`. `- Kind: child`, so S407/S408 do not apply.

RE-DEMONSTRATED THE PROBE DESIGN at this HEAD through the real `hsp._run_probe` (scratch `python3 -c`, nothing written):
`unshare -Urn true rc 0`; `('unshare', '-Urn') rc 0 | denied refused: [Errno 101] Network is unreachable | parent got b'HELLO' 0.199s`;
`('unshare', '-Ur') rc 4 | denied REACHED - not enforced | parent got b'HELLO' 0.186s`;
`('no-such-unshare-xyz', '-Urn') rc 127 | FileNotFoundError ... | parent got TimeoutError('timed out') 0.008s`. So the
probe CAN say yes on this host, the E-04/E-05 mechanism seams are reachable, and launcher failure is distinguishable.

Re-verified: `PRESENCE_VS_OBSERVATION` still has no consumer (one hit, its assignment); `x2dwu5` executed, `pi3bk8`
pending at `to-review`; `test_new_contract_fields_and_defaults` still couples `RUNNER_SAFETY_CAPABILITIES` to
`CONTRACT_FIELDS`; `host_cmd._capability_rows` still introspects `to_dict()`; `detect_host_capabilities` still calls
`probe_runner_safety_capabilities` under `plat == running_platform` before the certified-platform gate.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | MEDIUM | IN-SCOPE | Rubric C (operability), evidence currency | F-5 and OQ-02 ("once per opencode item dispatch (`oc_runipd._apply_execution_profile`...)"); `oc_runipd._apply_execution_profile` now calls `runner_shared.ensure_frozen_host_capabilities`; that function returns `state["host_capabilities"]` and probes only when absent; `HostSandboxCapabilities.from_dict` filters to known fields | The cost and blast-radius reasoning rested on a per-item probe that no longer exists; it is once per run. The plan also did not say what a resumed run with an older frozen descriptor reports (the new field defaults False, fail-closed). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 and OQ-02 corrected with the symbols; resumed-run behavior recorded; remaining multiplier (the test suite) named. |
| PR-102 | LOW | UNDER-SCOPE | Rubric E | V-03 "A green summary line is the evidence"; tests call `detect_host_capabilities` / `probe_runner_safety_capabilities` in ~45 places across 4 files | A bare "green" line does not distinguish pre-existing failures, and a new subprocess per call adds suite time nobody measured. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 bar is now the empty after-minus-before failing set; adds before/after wall time on the two host test files with a route to backlog if perceptible. |
| PR-103 | LOW | IN-SCOPE | Live-artifact convention | E-05 "That plan is `approved`"; `pi3bk8` reads `- Status: to-review` | Stated a drifting plan status as fact. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now a re-derive instruction with both observations as context. |
| PR-104 | LOW | IN-SCOPE | Ownership | Gate last sentence "the runner sets `graduated`" | Conflated graduation with the `done` close. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Names the graduating run and `runner_shared.evaluate_backlog_close` as the respective owners. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the frozen descriptor make the probe's uncached-ness moot for runs? | Yes for runs; the suite remains the multiplier, so measure it. | Leave per-item claim. REJECTED: false at HEAD. | `ensure_frozen_host_capabilities` docstring ("never probes per item"). | yes |

OQ-03 (naming) remains OPEN, `Blocking: no`, owner maintainer, carried by `wcbpqf`: a genuine maintainer naming call that
the field's mechanical renameability makes non-blocking. Not answerable from the repository. No finding left OPEN or DEFERRED.
