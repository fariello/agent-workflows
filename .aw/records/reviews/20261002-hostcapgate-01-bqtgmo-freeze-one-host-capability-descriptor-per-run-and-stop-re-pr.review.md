# Review: Freeze one host capability descriptor per run and stop re-probing on the dispatch path

- Subject-Id: bqtgmo
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before edits, and `--phase review-finalize` was clean after.

Re-verified at lane HEAD `990fb4aa`:

- The `_capture_turn_argv` swap (`subprocess.Popen = fake_popen`) and the `cmd[0]` allow-list are as described.
- The concurrent `subprocess.run(["true"])` worker reproduces: 22 successes and 76834 `stop-before-launch` refusals.
- `RUNNER_ACTION_TO_CONTRACT_ACTION == {}`, and all three runner actions map to `None`.
- The `execute_item_core` preflight block and its fail-open comment are present.
- Both hosts' `initialize_run` call `initialize_run_core`.
- `HostSandboxCapabilities.to_dict` is present.
- The carriers `y9m1ya`, `gqy7yd`, `oq05nc` and spec `25kzda` all resolve.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Correctness / premise (A, G) | `agent_workflows/oc_runipd.py:2325` `_apply_execution_profile` `capabilities = detect_host_capabilities("opencode")`, called from `run_opencode` at `argv = _apply_execution_profile(...)` | The per-turn probe is ALREADY LIVE on opencode. It runs on every turn regardless of profile, before `select_execution_profile` reads the request. The plan described this as "per turn for the hardened profile" and left it out of scope, so after execution the hazard would still reach every live oc turn. Measured: 3 default-profile calls -> 6 probe calls. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-06/V-06 and F-12. Added `oc_runipd.py` to Scope-Paths. E-06 makes no probe on the default profile and uses the frozen descriptor on hardened, keeps fail-closed `HardModeUnavailableError` even on a failed rehydration, and keeps `SandboxProfileError` reachable. Concern, Scope, Proposed changes, Over-scope and the gate text are reconciled. |
| PR-002 | MEDIUM | IN-SCOPE | Security / fail-closed (B) | plan E-02 shape (i) "delegate ... for any argv it did not expect, keeping the refusal only for the sentinel-bearing host argv" | Shape (i) inverts the default on the probing thread. An argv the probe fails to recognize would be LAUNCHED. That is the "launch a real agent host during a probe" outcome the plan itself calls far worse. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | Added the recommended shape (iii): delegate based on thread identity, so refusal stays unchanged on the probing thread. Recorded the hazard of shape (i). V-02 and the E-02 expected outcome require refusal of an unrecognized argv on the probing thread. |
| PR-003 | LOW | IN-SCOPE | Executability (G) | plan E-03/E-04 "durable run state" | No state key was named, so E-04 and E-06 could read a different key than E-03 writes. The new init-time cost on agy was also unmeasured. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 names a recommended key and a shape, uses the CLI host noun, and requires timing the measurement. V-03 asks for both. |
| PR-004 | LOW | IN-SCOPE | Execution contract (G) | plan gate POST-GATE LIFECYCLE | The gate did not say who runs finalize and did not forbid a hand `git mv`. The out-of-scope edit path was not stated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor ownership of `aw ipd finalize` and the rule that an out-of-scope edit is justified with `--scope-reason`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Fold the live oc per-turn probe into this plan, or file a separate one? | Fold in as E-06 | Separate plan (leaves the measured live hazard after this plan claims to stop re-probing); leave out of scope (the plan's own premise "unreached today" would be false) | `oc_runipd._apply_execution_profile`; `select_execution_profile` returns `default` without reading capabilities; seam count 6 calls / 3 turns | yes |
| D-2 | Recommended E-02 interception shape | Delegate based on thread identity | Delegate based on argv (fails open on an unrecognized argv); lock plus delegate (still argv-based) | `_capture_turn_argv` `fake_popen`; module fail-closed rule | yes |
