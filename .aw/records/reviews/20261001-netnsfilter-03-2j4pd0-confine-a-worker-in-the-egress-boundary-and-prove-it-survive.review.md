# Review findings: plan 2j4pd0

- Subject-Id: 2j4pd0
- Subject-Type: ipd
- Reviewed-At: 2026-10-10
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-800 (BLOCKER, fixed), PR-801 (HIGH, fixed), PR-802 (HIGH, fixed), PR-803 (MEDIUM, fixed), PR-804 (HIGH, open), PR-805 (HIGH, fixed), PR-806 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `0dd8c3a3e`. The plan was committed and byte-identical to the lane
input (sha256 prefix `ea6754651da13bf5`), so no pre-review snapshot. `aw ipd lint --phase author --agent` reported
`clean` before review. After review `--phase review-finalize --agent` reports exactly one finding, `IPD-Q501`, from the
deliberately escalated blocking OQ-04 (PR-804). `- Kind: child`, so IPD-S407/S408 do not apply. The run is a
driver-dispatched review lane with no human channel, so OQ-04 is left open (Step 3.3).

Evidence re-checked. Dependency `rozdkp` is in `executed/`; `egress_policy.EgressBroker`, `handle_broker_connection`
and `load_egress_policy` exist, and the broker is AF_UNIX-only. `host_sandbox_profile.enter_sandbox`,
`landlock_bootstrap_source`, `select_execution_profile`, `forced_runner_safety_verdicts`, `CAP_EGRESS_FILTERING`,
`supports_egress_filtering`, the `userns` refusal, and `oc_runipd._apply_execution_profile` (default returns `argv`
unchanged; "requires an isolated lane worktree") all resolve. `tests/test_host_sandbox_profile.py` carries
`EnterSandboxTests`, `ProfileDispatchTests.test_hard_mode_requested_without_capability_fails_closed` (patches `Popen`),
`AdversarialOsDenialTests` and `LandlockBootstrapTests`. `runner_shared.pinned_child_env` contains
`merged = os.environ.copy()`. Research `akmzyq` carries every quoted measurement (Findings 2, 3, 4, 6). The plan's quote
"Network scoping and container isolation are out of scope here" no longer exists in the module docstring (PR-806).

Measurements taken at review on this host (kernel 6.8, `unshare`, `setpriv`, `capsh`, `ip` present):

```text
# Landlock (this repo's bootstrap, _default_toolchain_roots) inside unshare -Urn, CAP_NET_ADMIN dropped:
in=net:[4026532755]
net:[4026531840]          <- systemd-run --user ... readlink /proc/self/ns/net : HOST namespace
systemd_run_rc=0
# capabilities retained: umount /run/user -> umount_rc=0 ; systemd-run -> host ns, rc 0 ; ip link add -> add_rc=0
# tmpfs over /run/user + setpriv --no-new-privs --inh-caps=-all --ambient-caps=-all --bounding-set=-all:
CapEff: 0000000000000000 / CapBnd: 0000000000000000
Failed to connect to bus: No such file or directory   (systemd_run_rc=1)
umount: /run/user: must be superuser to unmount.       (umount_rc=32)
RTNETLINK answers: Operation not permitted             (add_rc=2)
unshare: write failed /proc/self/uid_map: Operation not permitted
setns host netns: [Errno 13] Permission denied: '/proc/1/ns/net'
via /proc/PID/root: [Errno 13] Permission denied       (also under Landlock)
# capsh --drop=cap_net_admin only: nested unshare -Urn --map-root-user -> nested_add_rc=0
# AF_UNIX bind of a 139-byte path: OSError AF_UNIX path too long ; lane-scratch socket path = 161 bytes
# opencode models --refresh with HTTPS_PROXY -> proxy saw b'CONNECT models.opencode.ai:443 HTTP/1.1...' ; rc 0
# fresh netns /proc/<pid>/net/route: header only (no routes); /var/run/docker.sock present root:docker srw-rw----
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-800 | BLOCKER | UNDER-SCOPE | Security lens; Rubric B/D (boundary non-evadability) | Review measurement above: worker in `net:[4026532755]` obtained a process in host `net:[4026531840]` via `systemd-run --user` over `/run/user/1000/bus`; research `akmzyq` Finding 2 "unix socket across netns: PARENT-PROXY-REACHED" | AF_UNIX crosses the network namespace, which is what the broker relies on, so ANY reachable host socket (user systemd, D-Bus, docker, a forwarded ssh agent) lets the worker act outside the namespace. Nothing in E-01..E-06 hides them, so the plan as written ships a convention while its tests pass. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-07/V-07: mask host socket directories with fresh mounts, re-expose only the broker's directory, unset socket-naming env vars, no inherited socket fds; E-06/V-06 pin the host-service attempt and its inversion check; F-10 records the measurement. |
| PR-801 | HIGH | IN-SCOPE | Security lens (privilege) | Review measurement: with capabilities retained `umount /run/user` -> `umount_rc=0`; `capsh --drop=cap_net_admin` alone left `nested_add_rc=0`; full `setpriv` drop refused umount, `ip link add`, nested userns, `setns` | Dropping only `CAP_NET_ADMIN` leaves `CAP_SYS_ADMIN` in the user namespace, so the E-07 mask is removable and privilege can be rebuilt. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now drops every set (effective, permitted, inheritable, ambient, bounding) and sets `no_new_privs`; V-03 demands all five `Cap*` lines zero and `NoNewPrivs: 1` read by the driver, plus refused umount and nested unshare. F-11 added. |
| PR-802 | HIGH | UNDER-SCOPE | Rubric G (executability); right-sizing | `egress_policy.EgressBroker.start` binds `socket.AF_UNIX` only; OQ-01 resolves to "the standard proxy variables", which name a TCP endpoint; E-02 "The parent sets up loopback ... so the worker's relay target is reachable" names no relay | No component bridges the worker's TCP proxy connection to the AF_UNIX broker, and "the parent" conflates the driver (outside, must keep its network) with an in-namespace setup stage. An executor would have to invent both. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names the driver / setup-stage split. New E-08/V-08 builds the in-namespace relay in `egress_policy.py` (no policy decision; relay death yields no network). Measured that the real worker honors `HTTPS_PROXY` (F-12). |
| PR-803 | MEDIUM | IN-SCOPE | Rubric C (operability) | `oc_runipd._apply_execution_profile` keys scratch as `LANE_SCRATCH_SUBDIR / run_id / id6`; measured 161 bytes here; 139-byte bind -> `AF_UNIX path too long` | The natural socket location exceeds `sun_path` (108), so the broker would fail to start in a real lane. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires a short `0o700` directory reachable through the mask; V-02 demands the pasted path, length and mode. F-13 added. |
| PR-804 | HIGH | UNDER-SCOPE | Rubric G; public configuration contract | `egress_policy.load_egress_policy` raises "Egress policy configuration is absent ..."; `runner_profiles.ALLOWED_PROFILE_KEYS` is closed and its comment limits stored keys to "a NAME ... never a path, a root, an argv fragment, or a permission expression" | No artifact says where an operator declares the allow list, so E-04 cannot be executed without inventing a configuration surface; and the worker needs more than the model API host (F-12). The choice changes a published config boundary. | C:Medium; U:Medium-High; S:Medium; F:Medium; Overall:Medium-High | OPEN | Escalated as OQ-04 (`- Blocking: yes`, `- Finding: PR-804`) with options and a recommendation. `runner_profiles.py` and `tests/test_runner_profiles.py` added to Scope-Paths conditionally. |
| PR-805 | HIGH | IN-SCOPE | Rubric D (anti-regression); Set decision consistency | E-04 as written: hardened on a host whose egress probe reports False "must REFUSE"; orchestrator `m0kl28` OQ-01 "reported-only, with gating deferred to `wcbpqf`" | Every existing hardened run would start refusing on hosts without namespaces and on every host for lack of a policy, a silent behavior change contradicting the Set's own decision. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04: the boundary engages only when an allow list is declared; hardened without one is byte-unchanged; V-04 now demands five dispatch outcomes; Required tests extended. |
| PR-806 | LOW | IN-SCOPE | Evidence accuracy; OQ contract | Module docstring now reads "network denial is measured and cannot separate a git remote from the model API on one port, so none is applied"; OQ-01..03 had `- Owner: none` | Stale quoted sentence; owner field did not record who decided. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync re-quoted with a note that `wn956n` must re-anchor; owners set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the host AF_UNIX escape be closed? | Fresh mounts over host socket directories in the worker's mount namespace, re-exposing only the broker directory, plus env unset and no inherited fds. | (a) Landlock-only: rejected, Landlock ABI 4 here does not govern AF_UNIX connect (measured escape under the repo's own Landlock jail). (b) Enumerate and deny known sockets: rejected, default-allow. (c) seccomp filter on `connect(AF_UNIX)`: stronger but new machinery; left to the executor as an additional layer. | Review measurement (systemd-run escape; tmpfs mask blocked it). | yes |
| D-2 | Drop `CAP_NET_ADMIN` only, or every capability? | Every set plus `no_new_privs`. | Single-cap drop: rejected, measured `umount_rc=0` and `nested_add_rc=0`. | Review measurement; research `akmzyq` Finding 6. | yes |
| D-3 | Should hardened without an allow list be gated on the egress capability? | No: the boundary engages only when an allow list is declared. | Gate all hardened runs: rejected, contradicts `m0kl28` OQ-01 and regresses existing hardened runs. | `m0kl28` OQ-01; `load_egress_policy(None)` refusal. | yes |
| D-4 | How does a proxy-honoring worker reach an AF_UNIX broker? | An in-namespace TCP relay in `egress_policy.py`, a separate E-item. | Broker listening on TCP inside the namespace: rejected, it would put policy inside the confined namespace. Transparent REDIRECT: deferred by the plan already (carrier `sv9ce4`). | `EgressBroker.start` AF_UNIX-only; F-12 measurement. | yes |
| D-5 | Where should the broker socket live? | A short `0o700` directory, not lane scratch. | Lane scratch: rejected, 161 bytes exceeds `sun_path`. | Review measurement. | yes |
