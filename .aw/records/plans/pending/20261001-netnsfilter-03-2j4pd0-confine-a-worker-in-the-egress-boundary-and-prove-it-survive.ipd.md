# IPD: Confine a worker in the egress boundary and prove it survives teardown attempts

- Date: 2026-10-01
- Kind: child
- Concern: Children 01 and 02 deliver a probed partition and an enforcing broker, but nothing makes a real worker use either, so no boundary exists yet. This is also where the design can silently become a convention instead of a boundary: a worker placed in a namespace it created is root in that namespace and can delete the rules confining it. Measured during authoring (research `akmzyq` Finding 6), the naive arrangement was torn down in ONE command, `FLUSH SUCCEEDED`.
- Scope: Wire the egress boundary into the hardened execution profile so a confined worker reaches allow-listed destinations through the broker and nothing else, create the namespace in the PARENT, drop `CAP_NET_ADMIN` before handing off, and prove non-evadability by attempting teardown from inside and verifying refusal from OUTSIDE. Hardened remains opt-in and fails closed where the capability is absent.
- Scope-Paths: agent_workflows/host_sandbox_profile.py, agent_workflows/oc_runipd.py, agent_workflows/egress_policy.py, agent_workflows/runner_profiles.py, tests/test_host_sandbox_profile.py, tests/test_egress_confinement.py, tests/test_runner_profiles.py
- Item-Dependencies: executed:rozdkp
- Status: reviewed
- Readiness: no-go
- From-Backlog: sv9ce4
- From-Spec: 25kzda
- Work-Kind: feature
- Priority: low
- Set: netnsfilter
- Order: 3
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 2j4pd0

## Workflow history
- 2026-10-11 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-800, PR-801, PR-802, PR-803, PR-804, PR-805, PR-806. Reviewed at HEAD 0dd8c3a3e. Measured a host AF_UNIX escape (systemd-run --user reached the host netns) the original design left open: new E-07 socket mask, E-03 full capability drop, new E-08 in-namespace relay, E-04 engages only with a declared allow list. OQ-04 (blocking, maintainer): where the allow list is declared. Review record .aw/records/reviews/20261001-netnsfilter-03-2j4pd0-confine-a-worker-in-the-egress-boundary-and-prove-it-survive.review.md.
- 2026-10-07 to-review (aw set): returned to review: Set-level validation sweep owned by wn956n E-05/V-05; coverage pass recorded; open questions are non-blocking
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: Bare pytest run green with actual summary line pasted

- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `sv9ce4`. The non-evadability requirement in E-03 is the direct result of MEASURING the naive arrangement being torn down in one command during authoring, and then measuring the corrected arrangement refusing the same attempt (research `akmzyq` Finding 6).
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Turn the partition and the policy into an actual boundary around a real worker: allow-listed
destinations reachable, everything else refused, and the confinement not removable by the process it
confines, with that last property proven from outside rather than asserted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confinement

- [ ] E-01 Extend the sandbox plan and the launcher in `agent_workflows/host_sandbox_profile.py` to carry an OPTIONAL egress boundary: the policy object from child 02, the broker's AF_UNIX socket path, and nothing else. Default it OFF so every existing caller and every existing test is byte-unchanged, matching how `landlock_bootstrap_source` already defaults its parameters. When present, `enter_sandbox` must wrap the worker so it runs inside a network namespace whose only route out is the broker, composing with the existing Landlock filesystem rules rather than replacing them.
  - COMPOSITION IS MEASURED, NOT ASSUMED. Landlock reports ABI 4 INSIDE a network namespace on the authoring host (research `akmzyq` host table), so filesystem rules and namespace isolation coexist in one wrapper. That matters because `enter_sandbox` already builds a Landlock launcher and this item must not trade the filesystem partition for the network one.
  - Depends on: none
  - Expected outcome: `enter_sandbox` called without an egress boundary emits exactly today's launcher; called with one, it produces a worker confined on both axes. No default-path behavior changes.
  - Execution state: pending

- [ ] E-02 Create the namespace and install the policy IN THE PARENT, before the worker exists, and start the broker outside the namespace. The parent sets up loopback inside the namespace so the worker's relay target is reachable, holds the broker's AF_UNIX socket, and only then hands control to the worker. The worker must receive the broker's address through its environment or argv rather than discovering it, so the channel is explicit and auditable.
  - "THE PARENT" IS TWO PROCESSES, NAMED HERE SO THE EXECUTOR DOES NOT INVENT THE SPLIT (review PR-802). The DRIVER (`oc_runipd`, outside every namespace) owns the `EgressBroker` and its policy; it cannot itself enter the namespace without losing its own network. A short-lived SETUP STAGE, launched by the wrapper `enter_sandbox` returns (for example `unshare -Urnm --map-root-user` running a bootstrap), is privileged ONLY inside the new user, network and mount namespaces; it brings `lo` up, applies the E-07 socket mask, starts the in-namespace relay, drops every capability (E-03), applies Landlock, and then `execvp`s the worker. "Installed in the parent" therefore means: policy and broker in the DRIVER, namespace configuration in the SETUP STAGE before the worker's first instruction.
  - THE WORKER'S TCP ENTRY POINT is the in-namespace relay built by E-08; the setup stage starts it and exports `HTTPS_PROXY`/`HTTP_PROXY` (upper and lower case) naming it into the worker's environment, which is how OQ-01's resolution is carried out.
  - THE BROKER SOCKET PATH MUST FIT `sun_path` (review PR-803). A path under this worktree's lane scratch (`.aw/lane-scratch/<run>/<id6>/...`) measured 161 bytes, and a 139-byte bind failed with `OSError AF_UNIX path too long`; the Linux limit is 108 including the terminator. Place the socket in a short, parent-only (`0o700`) directory, and make it reachable from inside AFTER the E-07 mask hides the host's socket directories (for example by bind-mounting that one directory into the masked tree, or by reaching it through an inherited descriptor). Assert the length and the reachability in a test rather than assuming them.
  - ORDER IS LOAD-BEARING. Everything privileged must happen before the worker's first instruction, for the same reason `landlock_bootstrap_source` applies its ruleset before `execvp`: a boundary installed after the worker starts is a boundary the worker could have acted ahead of. Measured context: loopback inside the namespace works after `ip link set lo up` and needs no `slirp4netns` (research `akmzyq` Finding 2).
  - Depends on: E-01, E-08
  - Expected outcome: A worker that starts already confined, with the broker reachable and no other route out, and with every privileged setup step completed by the parent.
  - Execution state: pending

- [ ] E-03 DROP `CAP_NET_ADMIN` (and any other capability that permits altering network configuration) before handing off to the worker, so the confined process cannot modify what confines it. This is the item that makes the difference between a boundary and a convention, and it must be verified rather than assumed.
  - DROP EVERYTHING, NOT ONE CAPABILITY (review PR-801). The setup stage is root in its user namespace, so it also holds `CAP_SYS_ADMIN` there, and E-07's socket mask is only as durable as the worker's inability to unmount it. Clear the effective, permitted, inheritable, ambient AND bounding sets and set `no_new_privs` before `execvp`, so a setuid binary cannot regain anything. Measured at review with `setpriv --no-new-privs --inh-caps=-all --ambient-caps=-all --bounding-set=-all`: `CapEff: 0000000000000000`, `CapBnd: 0000000000000000`; `umount /run/user` -> `must be superuser to unmount` (`rc 32`); `ip link add d0 type dummy` -> `RTNETLINK answers: Operation not permitted`; a nested `unshare -Urm --map-root-user` -> `write failed /proc/self/uid_map: Operation not permitted`; `os.setns` on `/proc/1/ns/net` -> `[Errno 13] Permission denied`. By contrast `capsh --drop=cap_net_admin` alone left a nested `unshare -Urn --map-root-user` able to run `ip link add` (`nested_add_rc=0`) in a fresh namespace. That nested namespace has no route, so it is not an escape on its own, but a partial drop leaves the worker able to rebuild privilege and is not what this item ships.
  - THE NAIVE ARRANGEMENT IS EVADABLE IN ONE COMMAND, MEASURED. Research `akmzyq` Finding 6: a process placed in a namespace it created is root there, and flushing the filtering rules printed `FLUSH SUCCEEDED -> boundary is EVADABLE` with the rule gone afterwards. The CORRECTED arrangement, parent installs then drops the capability, was measured refusing the same attempt: `[agent] flush rc=4 out=iptables ... Permission denied (you must be root)`, with the parent's own post-attempt check showing the rule still present. BUILD THE SECOND ARRANGEMENT, never the first.
  - Depends on: E-02
  - Expected outcome: A confined worker whose attempt to alter the network configuration fails, with the confinement intact afterwards as seen from the parent.
  - Execution state: pending

- [ ] E-07 Close the HOST AF_UNIX ESCAPE: the setup stage must leave the worker no reachable host unix-domain socket other than the broker's, because an AF_UNIX socket crosses the network namespace (research `akmzyq` Finding 2, the very property the broker relies on) and a host service listening on one acts OUTSIDE the namespace on the worker's behalf. Mask the host's per-user and system socket directories with fresh empty mounts in the worker's mount namespace (at minimum `/run`, `/var/run`, `/tmp`, `/dev/shm` and `$XDG_RUNTIME_DIR`, re-exposing only the broker's directory), unset environment variables that name a host socket (`DBUS_SESSION_BUS_ADDRESS`, `SSH_AUTH_SOCK`, `XDG_RUNTIME_DIR`, `DOCKER_HOST` and similar), and ensure the worker keeps no inherited descriptor to such a socket. Abstract-namespace sockets are bound to the NETWORK namespace and are already unreachable; say so in the test rather than assuming it.
  - THIS IS A MEASURED, ONE-COMMAND ESCAPE IN THE PLAN AS FIRST WRITTEN (review PR-800). At review, inside `unshare -Urn --map-root-user` with `CAP_NET_ADMIN` dropped AND inside this repository's own `landlock_bootstrap_source` jail built from `_default_toolchain_roots()`, the worker reported its own namespace `net:[4026532755]`, then ran `systemd-run --user --wait --pipe -q readlink /proc/self/ns/net`, which printed the HOST namespace `net:[4026531840]` with `rc=0`. The command reached the user systemd manager over `/run/user/1000/bus`, which nothing in the original E-01 to E-06 hides (`/run/user` is not a Landlock-governed connect target, and `/etc`, `/usr` and `/proc` are read-only roots). A process spawned that way has the HOST's network and none of the boundary, so the confinement this plan proves with E-05 and E-06 would be a convention. After a fresh `tmpfs` over `/run/user` and a full capability drop the same command failed `Failed to connect to bus: No such file or directory`, `systemd_run_rc=1`. Without the full drop of E-03 the mask is removable: with capabilities retained `umount /run/user` returned `umount_rc=0`, after which the escape worked again.
  - DOCKER IS THE SAME CLASS: `/var/run/docker.sock` is present on the review host (`root:docker`, mode `srw-rw----`). The reviewing user is not in the `docker` group, but on a host where the operator is, that socket is root on the host. The mask must cover it by construction, not because one host happens to deny it.
  - Depends on: E-03
  - Expected outcome: Inside the confined worker no host AF_UNIX socket other than the broker's is connectable, `systemd-run --user` and any D-Bus or Docker client fail to reach their host service, the mask cannot be unmounted, and the broker path still works.
  - Execution state: pending

- [ ] E-04 Wire the boundary into `oc_runipd._apply_execution_profile` so the `hardened` profile applies it, preserving the existing fail-closed posture exactly: `select_execution_profile` already raises `HardModeUnavailableError` rather than degrading when hardened is unavailable, and hardened already refuses without an isolated lane. Requesting hardened on a host whose EXECUTED egress probe reports False must REFUSE, never silently run unfiltered. Leave the default profile byte-unchanged, so nothing changes for a run that did not ask for hardening.
  - DO NOT WEAKEN CHILD 01'S FAIL-CLOSED PATH to make hardened reachable on an incapable host. The correct outcome there is that hardened egress filtering is unavailable and says so, which is the established pattern in this module rather than a new one.
  - THE BOUNDARY ENGAGES ONLY WHEN AN ALLOW LIST IS DECLARED, so a hardened run that declares none is BYTE-UNCHANGED (review PR-805). As first written, this item made every `hardened` request depend on `supports_egress_filtering`, which (a) silently changed behavior for hardened runs that never asked for egress filtering, refusing them on a Landlock-capable host where the namespace cannot be created (the `uq4y6q` host) and refusing them everywhere for lack of a policy, since `egress_policy.load_egress_policy(None)` raises `PolicyConfigurationError`; and (b) contradicted orchestrator `m0kl28` OQ-01, resolved "reported-only, with gating deferred to `wcbpqf`". Corrected rule: hardened WITHOUT a declared allow list applies today's Landlock launcher exactly; hardened WITH one requires `supports_egress_filtering` True and otherwise raises `HardModeUnavailableError`; a declared but unparseable allow list raises `PolicyConfigurationError` BEFORE any spawn. The allow list is the operator's opt-in to egress filtering, so refusing on it is the fail-closed answer to a request, not a gate on the hardened profile. WHERE the allow list is declared is OQ-04 (blocking).
  - Depends on: E-03, E-07
  - Expected outcome: `hardened` with a declared allow list gains egress filtering where the probe proved the capability and refuses loudly where it did not; `hardened` without one, and the default profile, are unaffected.
  - Execution state: pending

- [ ] E-08 Add the IN-NAMESPACE RELAY to `agent_workflows/egress_policy.py`, beside the broker (split out of E-02 at review for right-sizing, PR-802: it is a separate deliverable with its own test surface). Standard proxy variables name a TCP endpoint and the broker listens on AF_UNIX, so something inside the namespace must listen on `127.0.0.1:<port>` and forward each accepted connection byte-for-byte to the broker socket. It makes NO policy decision (the broker in the driver decides), so killing or subverting it yields no network, never unfiltered network (F-6). Bound it with the same timeouts as the broker and make it a callable the setup stage can start before `execvp`.
  - Measured at review that the shipped worker honors the variable: `opencode models --refresh` with `HTTPS_PROXY` set issued `CONNECT models.opencode.ai:443 HTTP/1.1` to the proxy and exited `rc 0` (F-12).
  - Depends on: none
  - Expected outcome: A relay that forwards a CONNECT from a TCP loopback client to the AF_UNIX broker unchanged, so the broker's allow and refuse decisions reach the client intact, testable without a namespace.
  - Execution state: pending

### Task group 2: proof

- [ ] E-05 Add `tests/test_egress_confinement.py` proving the boundary end to end with a REAL subprocess, using parent-held endpoints so the test needs no external network: a confined worker reaches an allow-listed destination and is REFUSED for an unlisted one on the SAME port. Also assert the default profile's argv is unchanged, so the additive guarantee is pinned rather than claimed. Skip only where the host cannot create a namespace, and make that skip state WHICH guarantee is consequently unverified.
  - Depends on: E-04
  - Expected outcome: The same-port destination partition is pinned by a test driving a real confined process, which is the property no existing test in this repository covers.
  - Execution state: pending

- [ ] E-06 Add the ADVERSARIAL test: a confined worker attempts to escape and each attempt is verified to fail, modeled on the existing `AdversarialOsDenialTests` in `tests/test_host_sandbox_profile.py`, which already proves filesystem denials this way. Cover the attempts measured during authoring: tearing down the filtering rules; connecting directly to a denied destination by raw address; reaching a denied destination on a different port; and nesting a fresh namespace to escape. ALSO cover the two measured at review (PR-800, PR-801): reaching a HOST service over an AF_UNIX socket (`systemd-run --user ... readlink /proc/self/ns/net`, judged by whether the spawned process reports the host's network namespace, and a direct connect to the host's per-user bus path), and unmounting the E-07 mask. "Tearing down the filtering rules" means altering the namespace's network configuration (for example `ip link add`, `ip route add`, or an `iptables`/`nft` change); this plan's design installs no packet-filter rules, so read the namespace's links and routes from the DRIVER afterwards (`/proc/<worker-pid>/net/route` and `/proc/<worker-pid>/net/dev` are readable from outside) instead of trusting the worker's report. VERIFY EVERY OUTCOME FROM OUTSIDE the sandbox, never by asking the confined process whether it is still confined.
  - FIVE EVASIONS WERE MEASURED HOLDING (research `akmzyq` Finding 4): proxy variables removed gave `Could not resolve host: github.com`; a raw-address CONNECT was refused `403`; port 22 was refused `403`; a nested `unshare` still reported `Network is unreachable`; and the allow-listed destination still succeeded with `rc: 0`. That last row is part of the test, not a footnote: a boundary that also breaks the model API is not a product.
  - A METHODOLOGY TRAP WORTH NAMING, because it nearly produced a false pass during authoring: the first version of the teardown measurement piped `iptables` through `head`, so the pipeline's exit status masked the real one and it printed `FLUSH SUCCEEDED` for a flush that had actually been REFUSED. Do not judge a teardown attempt by a piped command's exit status; read the rules from the parent afterwards.
  - Depends on: E-05
  - Expected outcome: Each evasion attempt, including the host-socket and unmount attempts, is pinned as refused, with the refusal established by the parent's own view, and the allow-listed path still working.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `_apply_execution_profile` returns `argv` UNCHANGED for the default profile, which is "what keeps
  this phase strictly additive: no default-path behavior is altered". This plan preserves that exactly.
- Hardened mode already FAILS CLOSED in two ways worth matching rather than reinventing:
  `select_execution_profile` raises `HardModeUnavailableError` instead of returning `"default"`, and
  `_apply_execution_profile` raises `SandboxProfileError` when hardened is requested without an
  isolated lane because "there would be no lane boundary to enforce".
- The OpenCode runner is the ONLY host that applies an execution profile. `oc_runipd` records that
  `agy_runipd` "contains zero references to `execution_profile`, `host_sandbox_profile`,
  `runner_profiles`, `resolve_launch_profile` or `launch_profile`", so an agy run silently ignores a
  stored request. This plan changes that asymmetry not at all and must not imply otherwise.
- `enter_sandbox` applies the Landlock ruleset BEFORE `execvp`, and the bootstrap's own docstring notes
  that Landlock domains "are inherited across `fork`/`exec` and cannot be relaxed", so "a
  shell-capable worker cannot escape by spawning children". E-02 follows the same ordering discipline
  for the network boundary.
- `enter_sandbox` REFUSES the `userns` mechanism outright because a bare user namespace "enforces no
  per-path partition" and would fail OPEN. The lesson is that a namespace alone is never the boundary;
  what confines is the policy plus the capability drop.
- Adversarial denial tests already exist in this repository and are the model to follow:
  `AdversarialOsDenialTests` proves a hardened worker's writes to the control, main and sibling trees
  are denied BY THE OS rather than by convention.
- A skip is not acceptance evidence: a skip "leaves the guarantee UNVERIFIED on that machine".
- A test must exercise behavior, never pin code structure (AGENTS.md P16).
- Cite code by SYMBOL or quoted content string, never by a bare line number (`IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | THE NAIVE ARRANGEMENT IS EVADABLE IN ONE COMMAND | Research `akmzyq` Finding 6: a process root in its own namespace flushed the filtering rules, printing `FLUSH SUCCEEDED -> boundary is EVADABLE`, with `-P OUTPUT ACCEPT` and no rule afterwards | E-03 is the single most important item in this Set. Without the capability drop this plan ships a convention while describing a boundary. |
| F-2 | THE CORRECTED ARRANGEMENT HOLDS, verified from the parent | Research `akmzyq` Finding 6: after the parent installed the policy and dropped `CAP_NET_ADMIN`, the worker's attempt returned `flush rc=4 ... Permission denied (you must be root)` and the parent's own post-attempt check still showed the rule present | The fix is demonstrated, not proposed. It also sets the evidence standard: the authoritative check is the PARENT's view, not the confined process's report. |
| F-3 | A piped exit status produced the WRONG verdict during authoring | Research `akmzyq` Finding 6 methodology note: piping `iptables` through `head` masked the exit status and printed `FLUSH SUCCEEDED` for a flush that had been REFUSED | E-06 forbids judging a teardown by a piped command's status. A probe that reports the wrong answer in the SAFE direction is still broken, and this one argued against building a mechanism that works. |
| F-4 | Five evasion attempts were measured holding | Research `akmzyq` Finding 4: `Could not resolve host` with proxy vars removed; raw-address CONNECT refused `403`; port 22 refused `403`; nested `unshare` still `Network is unreachable`; allow-listed host still `rc: 0` | E-06's test list is this table. The last row is a requirement and not a footnote: a boundary that denies the model API denies the product. |
| F-5 | Landlock composes with a network namespace in one wrapper | Research `akmzyq` host table: Landlock ABI reported `4` both outside and INSIDE a namespace | E-01 may add the network axis without trading away the filesystem partition `enter_sandbox` already builds. |
| F-6 | An uncooperative worker gets NO network rather than a bypass | Research `akmzyq` Finding 4 row 1: a direct `git ls-remote` with every proxy variable removed failed with `Could not resolve host: github.com`, because the namespace has no route | The boundary does not depend on the worker honoring configuration, which is what makes it a boundary. E-02 must therefore ensure the namespace genuinely has no other route. |
| F-7 | Loopback inside the namespace needs no `slirp4netns` | Research `akmzyq` Finding 2: after `ip link set lo up`, a bind and connect on `127.0.0.1` succeeded inside the namespace; AF_UNIX reached the parent in the same run | E-02 needs no veth, bridge, NAT or extra dependency. Note `slirp4netns` was INSTALLED on `uq4y6q`'s host where namespaces did not work at all, so its presence proves nothing. |
| F-8 | Only the OpenCode runner applies an execution profile | `oc_runipd`'s own comment records that `agy_runipd` has zero references to `execution_profile` or `host_sandbox_profile`, so an agy run silently ignores a stored request | E-04 wires one host. The Set must not describe the boundary as covering every host, and child 04's audit should catch it if any artifact does. |
| F-10 | AN AF_UNIX SOCKET TO A HOST SERVICE IS AN ESCAPE THE ORIGINAL DESIGN LEFT OPEN (measured at review) | Inside `unshare -Urn --map-root-user`, `CAP_NET_ADMIN` dropped, under this repo's own `landlock_bootstrap_source` jail from `_default_toolchain_roots()`: the worker's namespace was `net:[4026532755]`, and `systemd-run --user --wait --pipe -q readlink /proc/self/ns/net` printed the host's `net:[4026531840]`, `rc=0`, over `/run/user/1000/bus` | E-07 masks host socket directories; E-06 pins the attempt. The same property that lets the broker work (Finding 2) lets any host socket work, so the boundary is only as strong as the set of sockets the worker can reach. |
| F-11 | THE MASK HOLDS ONLY UNDER A FULL CAPABILITY DROP (measured at review) | With capabilities retained, `umount /run/user` -> `umount_rc=0` and the escape returned. Under `setpriv --no-new-privs --inh-caps=-all --ambient-caps=-all --bounding-set=-all`: `CapEff` and `CapBnd` all zero, `umount` refused `must be superuser`, `ip link add` refused, nested `unshare -Urm` refused at `uid_map`, `setns` on `/proc/1/ns/net` `Permission denied`, and a connect via `/proc/<host-pid>/root/run/user/1000/bus` `Permission denied` | E-03 drops every capability rather than `CAP_NET_ADMIN` alone. |
| F-12 | The real worker honors the proxy variable (measured at review) | `opencode models --refresh` with `HTTPS_PROXY` set issued `CONNECT models.opencode.ai:443 HTTP/1.1` to the proxy and exited `rc 0` | OQ-01's environment channel works for the shipped worker. It also shows the allow list needs more than the model API host: an allow list naming only the model provider would break the worker's own model-catalog fetch, which is why OQ-04 is the operator's decision. |
| F-13 | The broker's socket path must be short | A path under this lane's `.aw/lane-scratch/<run>/<id6>/` measured 161 bytes; a 139-byte AF_UNIX bind failed `OSError AF_UNIX path too long` | E-02 places the socket in a short parent-only directory, not in lane scratch. |
| F-9 | The hardened profile is OPT-IN and has no CLI flag | `_apply_execution_profile` returns `argv` unchanged unless `execution_profile` is `hardened` in the operator's own `runner-profiles.json`; the deliberate absence of a flag is recorded because "a documented flag on a cross-platform tool reads as a cross-platform guarantee" | Nothing changes for a default run, which bounds this plan's blast radius. It also means the boundary protects only runs that asked for it, which child 04 must state honestly. |

## Proposed changes (ordered, validatable)

1. Carry an optional egress boundary through the sandbox plan and launcher, defaulted off so the
   default path is byte-unchanged (E-01).
2. Build the in-namespace TCP relay that forwards to the AF_UNIX broker (E-08).
3. Create the namespace, install the policy, and start the broker in the PARENT before the worker
   exists, with the driver/setup-stage split named (E-02).
4. Drop EVERY capability and set `no_new_privs` before handing off, which is what makes the
   confinement non-evadable (E-03).
5. Hide every host AF_UNIX socket except the broker's, closing the host-service escape measured at
   review (E-07).
6. Wire it into the hardened profile only when an allow list is declared, preserving the existing
   fail-closed refusals and leaving hardened-without-allow-list byte-unchanged (E-04, OQ-04).
7. Pin the same-port destination partition with a real confined subprocess (E-05).
8. Pin every measured evasion as refused, verified from outside the sandbox (E-06).

## Deferred / out of scope (with reason)

- THE ANTIGRAVITY HOST. `agy_runipd` applies no execution profile at all (F-8), so wiring it is a
  separate piece of work on a host that today ignores the request entirely.
  - Carrier: sv9ce4
- TRANSPARENT REDIRECT interception, measured working against a hostile raw-socket client (research
  `akmzyq` Finding 5). Not built here because F-6 shows an uncooperative worker already gets no
  network, so the namespace's lack of a route provides the property this would strengthen.
  - Carrier: sv9ce4
- GATING any action on the capability, and reintroducing a finding code. Both are maintainer decisions
  and neither is needed for the boundary to work.
  - Carrier: wcbpqf
- MAKING hardened the DEFAULT profile, or adding a CLI flag for it. Deliberately untouched: the absence
  of a flag is a recorded decision, on the grounds that a documented flag on a cross-platform tool
  reads as a cross-platform guarantee, and this plan's mechanism is Linux-only.
  - Carrier-Declined: NOT WANTED and not owed. Changing the default would alter behavior for runs that
    never asked for a boundary, on a mechanism that fails closed off Linux, and the current opt-in
    posture is a deliberate choice rather than an unfinished one.
- WITHHOLDING environment-carried credentials such as `GH_TOKEN` or a forwarded `SSH_AUTH_SOCK`, which
  `runner_shared.pinned_child_env` passes through because it is an `os.environ.copy()`. RELEVANT HERE
  and stated so a reader does not over-read this plan: a push-capable token still reaches the worker,
  and what this plan removes is the worker's ROUTE to a denied remote, not its credentials. E-07 does
  unset `SSH_AUTH_SOCK` and hide its directory, because a forwarded agent socket is a HOST AF_UNIX
  socket and therefore an escape route, but that is a side effect of closing the route, not a
  credential-withholding feature, and `GH_TOKEN`-style values in the environment are untouched.
  - Carrier: sv9ce4

## Scope check

- Over-scope: none. `host_sandbox_profile.py` is changed by E-01 through E-03 and E-07 (the setup
  stage, capability drop and socket mask); `oc_runipd.py` by E-04 (driver-side broker lifetime and
  dispatch); `egress_policy.py` by the in-namespace relay of E-02 and whatever the broker needs to be
  startable by the driver at launch; `runner_profiles.py` and `tests/test_runner_profiles.py` ONLY if
  OQ-04 places the allow list in `runner-profiles.json` (otherwise acknowledge them at finalize as
  declared-but-unmodified); `tests/test_host_sandbox_profile.py` by the default-path-unchanged
  assertion in E-05; `tests/test_egress_confinement.py` is NEW.
- Under-scope: none. `agy_runipd.py` is deliberately NOT declared and NOT changed (F-8): it applies no
  execution profile, so an edit there would be new host-support work rather than this plan's wiring. No
  spec or docstring amendment is declared either, because child 04 owns both and must write them
  against the limits this plan MEASURES rather than the ones it predicts.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. This plan changes the
  launcher and the OpenCode runner, so the suite is the primary gate.
- `tests/test_egress_confinement.py` must pass on a host that can create a namespace. If the host
  cannot, paste the skip reason and state explicitly which guarantee is unverified, since a skip is not
  acceptance evidence.
- The DEFAULT profile's argv, and the HARDENED profile's launcher when no allow list is declared, must
  be proven unchanged, pasted, since that is what keeps this plan additive (PR-805).
- `aw ipd lint` conforming. `aw check` reporting no new finding naming this plan's artifacts, judged as
  a delta rather than by exit code, since it exits nonzero today on pre-existing findings.
- `aw sanitize --agent` exits zero. Namespace and broker output can carry host paths, and this plan
  pastes a great deal of both.

## Spec / documentation sync

- NO SPEC EDIT IN THIS PLAN and no spec path declared, deliberately. Spec `25kzda` 5.2 requires
  descriptor entries be "backed by positive and fail-closed probe evidence", and the honest statement
  of what this boundary covers depends on what THIS plan measures. Child 04 writes it immediately
  after, with the measurements in hand, which is the ordering that prevents a contract describing a
  hoped-for capability.
- `host_sandbox_profile`'s module docstring states network denial "cannot separate a git remote from
  the model API on one port, so none is applied", which this plan makes false for a hardened run with a
  declared allow list (re-quoted at review: the older sentence "Network scoping and container isolation
  are out of scope here" no longer exists, and child `wn956n` E-01 still quotes it and must re-anchor). Child 04 amends it in the same pass as the spec so the two
  cannot drift. That is a known, deliberate, one-child window and not an oversight.
- `docs/runner-profiles.md` documents the hardened profile for operators and will need the egress
  boundary described, including that it is Linux-only, opt-in, and OpenCode-only. Child 04 owns it,
  for the same reason: operator documentation written before the limits are measured is the overclaim
  this Set exists to avoid.
- Child 04 must also state the limits review measured here: the boundary depends on the socket mask
  (E-07) as much as on the capability drop, so a host AF_UNIX service the mask does not cover is a
  route out; and the allow list must include whatever the worker itself fetches (F-12). Neither is
  editable from this review's scope; `wn956n` should re-anchor on this plan's measured V-07 evidence.
- No CHANGELOG entry here: child 04 records the Set's user-visible change once.

## Open questions

### OQ-01: Should the worker receive the broker address through the environment or through argv?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: the environment, because the worker is an off-the-shelf
  agent process whose argv this repository does not control, and the standard proxy variables are the
  mechanism such a process already honors. Measured during authoring, a `curl` and a real `git` both
  routed through the broker via environment configuration (research `akmzyq` Finding 3). The obvious
  objection is that an agent can unset an environment variable, and it is ANSWERED BY MEASUREMENT
  rather than by trust: doing so does not yield a bypass, it yields no network, because the namespace
  has no route (Finding 4 row 1, `Could not resolve host: github.com`). So the environment is a
  convenience for the cooperative path and not the thing that enforces the boundary.

### OQ-02: Must the broker be one per worker, or may one broker serve several confined workers?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: one broker per confined worker, matching how the lane
  scratch directory is already keyed per run and per item so "a retry or a co-resident lane never
  collides". A shared broker would make one worker's policy and decision log depend on another's
  lifetime, which breaks the per-item attribution the runner's evidence model relies on, and it would
  turn broker termination into a cross-lane concern. The cost is one AF_UNIX socket and one listener
  per confined worker, which is negligible beside the subprocess the worker already is. A later plan
  wanting a shared broker would need to solve per-item attribution first.

### OQ-03: What should happen when the broker dies mid-turn?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM THE NAMESPACE'S OWN BEHAVIOR: the worker loses all
  egress, which is the fail-closed direction and requires no additional mechanism. Because the
  namespace has no route (F-6), a dead broker means destinations become unreachable rather than
  unfiltered, so the dangerous failure (traffic escaping unchecked) is not reachable by killing the
  broker. What this plan DOES owe is distinguishability, which E-04 of child 02 already requires for
  refusals: a broker that has died must not look like a policy refusal, so the worker's failure should
  be reported as an infrastructure fault. That is a reporting concern rather than a safety one, and it
  is why this question is non-blocking.

### OQ-04: Where does an operator declare the egress allow list, and what must it contain for the worker to function?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-804
- Context: E-04 needs a policy object, and `egress_policy.load_egress_policy(None)` refuses by design ("Egress policy configuration is absent: explicit policy configuration is required and cannot be defaulted or guessed"). No artifact in the Set says where that configuration comes from. `runner_profiles.ALLOWED_PROFILE_KEYS` is a closed set (`runner`, `model`, `variant`, `agent`, `validate`, `verify_with`, `execution_profile`), and its own comment draws the safety line at "a NAME drawn from a two-member vocabulary this module owns, never a path, a root, an argv fragment, or a permission expression". An allow list of destinations is closer to a permission expression than to a name, so adding one there changes that published boundary, which is a contract decision. Measured at review (F-12), the real worker fetches `models.opencode.ai:443` on start-up in addition to the model provider, so an allow list naming only the provider would break the product.
- Options: (A) a new per-profile key in the operator's `runner-profiles.json`, for example `egress_allow`, validated by `load_egress_policy` at profile load and frozen into run options like `execution_profile` (touches `runner_profiles.py`, declared in Scope-Paths); (B) a separate operator file under the user config directory, read only when `execution_profile` is `hardened`; (C) no operator configuration in this plan: ship the mechanism with a test-only policy and leave hardened runs unfiltered until a follow-up plan decides the source (E-04 then wires nothing and the Set's completion criterion for a real worker moves to that plan).
- Recommendation: (A), because it reuses the existing frozen-options path and keeps the request beside the `execution_profile` it qualifies, with the module comment amended to say why a destination list is admissible there. The operator documents the required entries; this repository must not guess them (child 02 E-02).
- Resolution or deferral rationale: OPEN. Raised at review because the answer changes a published configuration surface and this plan's scope; the repository cannot answer it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted proof that `enter_sandbox` called WITHOUT an egress boundary produces byte-identical output to today's, for example a captured digest compared before and after, plus the pasted result of the existing `EnterSandboxTests` and `LandlockBootstrapTests` still passing. Then the launcher produced WITH a boundary, showing both the Landlock rules and the namespace wrapper present in one launch path.
  - PROVE THE FILESYSTEM PARTITION SURVIVED. Paste the existing `AdversarialOsDenialTests` passing, since those are what prove a hardened worker cannot write the control, main or sibling trees. Adding a network axis must not cost the axis this repository already had, and a green overall suite alone does not demonstrate that specifically.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted evidence that every privileged setup step completed in the PARENT before the worker started: the namespace created, loopback up, the policy installed, the broker listening. Show the ordering, for example by the parent's own log timestamps or a sequenced test assertion, plus the broker address as the worker received it.
  - Paste the broker socket path, its byte length (under 108), and its directory mode (`0o700`), and show the worker reaching the broker through the E-08 relay via `HTTPS_PROXY` (F-13).
  - PROVE THE NAMESPACE HAS NO OTHER ROUTE OUT, which is what F-6 rests on and what makes the boundary independent of worker cooperation. Paste a direct outbound attempt from inside the namespace with NO proxy configuration showing it fails, and state the error verbatim.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output of the confined worker attempting to tear down its own boundary, showing the attempt REFUSED with its exact error, followed by the PARENT's own check showing the filtering configuration still intact. Both halves are required: the refusal alone does not prove the rules survived.
  - THE AUTHORITATIVE CHECK IS THE PARENT'S, AND A PIPED EXIT STATUS IS NOT EVIDENCE. Do not judge the teardown by a piped command's status: during authoring exactly that masked the real status and printed `FLUSH SUCCEEDED` for a flush that had been REFUSED (F-3). Paste the parent's unpiped view of the rules after the attempt, and state explicitly that the verdict came from outside the sandbox.
  - ALSO CONFIRM EVERY CAPABILITY IS ACTUALLY GONE rather than merely unused: paste the worker's `CapEff`, `CapPrm`, `CapInh`, `CapAmb` and `CapBnd` lines from `/proc/<worker-pid>/status` READ BY THE DRIVER (all must be zero) and `NoNewPrivs: 1`, plus the refused results of `umount` on a masked directory and of a nested `unshare -Urm --map-root-user` (PR-801). One refused `ip` command is not this evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted proof of five dispatch outcomes: the DEFAULT profile returning argv unchanged; `hardened` WITHOUT a declared allow list returning exactly today's Landlock launcher (PR-805); `hardened` with an allow list on a capable host producing a confined launcher; `hardened` with an allow list on a host whose egress probe reports False REFUSING with the existing fail-closed error rather than running unfiltered; and a declared but unparseable allow list raising `PolicyConfigurationError` before any spawn. Force the third through the `forced_runner_safety_verdicts` seam rather than requiring an incapable host, so it is verified on every machine including this one.
  - NOTHING MAY SPAWN IN EITHER REFUSAL CASE. Follow the pattern of the existing `test_hard_mode_requested_without_capability_fails_closed`, which patches `Popen` to prove no process starts. A refusal that still launched the worker unfiltered would be the exact fail-open outcome this item exists to prevent, and a raised exception alone does not rule it out.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted test output showing a REAL confined subprocess reaching an allow-listed destination and being REFUSED for an unlisted one ON THE SAME PORT, with the client-side result for each. A pair differing in port does not meet this item, because that is a decision the Landlock mechanism could already make and would not demonstrate this Set's reason to exist.
  - If the test SKIPPED because the host cannot create a namespace, paste the skip reason and state plainly which guarantee is consequently unverified here. Do not let a green summary line stand in for a skipped boundary test.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted result for EACH of the six evasion attempts (network-configuration teardown, raw-address connect, denied destination on another port, nested namespace, host-service reach over AF_UNIX, unmounting the socket mask), each showing the attempt failed and each verified from OUTSIDE the sandbox (for the host-service row: the namespace id any spawned process reports, compared by the driver against the host's own). Plus the fifth row: the allow-listed destination still succeeding, which proves the boundary did not take the product with it.
  - PROVE THE ADVERSARIAL TESTS ARE NOT VACUOUS. Temporarily remove the capability drop so the naive arrangement is restored, paste the resulting FAILURE of the teardown test, then revert and paste the restored pass. Do the same for the socket mask: remove E-07's mask, paste the host-service test FAILING (at review this arrangement printed the host's `net:[4026531840]`), then revert and paste the pass. F-1 measured that arrangement succeeding in one command, so a test suite that stays green against it is not testing non-evadability at all, and that is the single defect most likely to ship unnoticed from this plan.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: Pasted output, from a test driving a REAL confined worker, of: (a) the worker's attempt to connect to every AF_UNIX socket path it can find by walking its visible filesystem, listing every path that CONNECTED (only the broker's may appear); (b) `systemd-run --user --wait --pipe -q readlink /proc/self/ns/net` (or, where `systemd-run` is absent, a direct connect to the host's `$XDG_RUNTIME_DIR/bus` path captured by the driver before launch) FAILING, with its error verbatim; (c) the worker's environment showing `DBUS_SESSION_BUS_ADDRESS`, `SSH_AUTH_SOCK`, `XDG_RUNTIME_DIR` and `DOCKER_HOST` unset; and (d) the broker path still working in the same run.
  - Bound the filesystem walk (skip `/proc` and `/sys`, cap depth or time), because an unbounded walk of `/` timed out at 120 s during review. If the host has no user bus at all, say so and state that row (b) is consequently unverified here.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: Pasted test output, with no namespace, showing a TCP loopback client sending `CONNECT` through the relay to a live `EgressBroker`: an allow-listed destination TUNNELLED (bytes reach the parent-held listener) and an unlisted one on the SAME port REFUSED with the broker's own distinguishable refusal, unchanged by the relay. Plus the relay's behavior when the broker socket is gone: the client gets a connection failure, never a direct connection to the destination (show the destination listener received nothing).
  - Observed evidence:
  - Result: pending



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This is the plan where the Set either delivers a boundary or ships a convention, and review measured
that the difference is TWO things, not one: the capability drop (E-03) and hiding every host AF_UNIX
socket (E-07). With `CAP_NET_ADMIN` dropped and Landlock applied, the original design still let the
worker run `systemd-run --user` and obtain a process in the HOST network namespace (F-10). A reviewer
should treat E-03, E-07 and V-06 as the center of the plan: research
`akmzyq` Finding 6 measured the naive arrangement being dismantled by the confined process in a single
command, and a plan that omitted the drop would still pass a functional test of filtering, still
produce convincing allowed and refused evidence, and be worthless as a boundary.

WHAT A REVIEWER SHOULD PUSH HARDEST ON. First, that the teardown verdict is read from the PARENT and
never from the confined process, and that no piped exit status is trusted for it, because that exact
mistake produced the wrong answer during authoring (F-3). Second, that V-06's inversion check is
actually performed: restoring the naive arrangement must make the test FAIL, and if it does not, the
test is not measuring what it claims. Third, that the filesystem partition this repository already had
is not traded for the network one, which V-01 checks by re-running the existing adversarial denial
tests specifically rather than relying on a green suite. Fourth, that the refusal path spawns nothing,
following the existing `Popen`-patching precedent.

ONE HONEST BOUND TO KEEP IN VIEW while reviewing: this plan removes the worker's ROUTE to a denied
remote, not its CREDENTIALS. A `GH_TOKEN` or forwarded `SSH_AUTH_SOCK` still reaches the worker because
`runner_shared.pinned_child_env` is an `os.environ.copy()`, and the boundary applies only to runs that
opted into `hardened` on the OpenCode host. Neither fact weakens the plan, and both must stay out of
any sentence that describes what it delivers.

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`,
never `git add -A`, and never push. This is a SHARED CHECKOUT: verify the staged set with
`git diff --cached --name-only` before committing, unstage anything that is not yours with
`git restore --staged <path>`, and re-verify after any failed raw commit attempt. Run the suite BARE
as `python3 -m pytest` and PASTE ITS ACTUAL SUMMARY LINE; a summary you did not produce is not
evidence, and the same hard-MUST governs every pasted refusal, parent-side rule listing, and exit
status these `V-*` items demand. Paste skips explicitly rather than letting a green line hide one.

LIFECYCLE TRANSITION. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete observed evidence.
Reaching `executed/` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` /
`aw agy run` the RUNNER owns the terminal transition and finalize, so do NOT invoke `aw ipd finalize`
yourself in a runner-driven execution; a HAND execution invokes it
(`aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`). Never hand-edit
`- Status:` and never hand-roll a `git mv` into `executed/`. This plan must NOT set backlog `sv9ce4`
to `done`; the runner sets `graduated`.
