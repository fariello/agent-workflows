---
id: uq4y6q
created: 20260929
set: denypush
order: 00
topic: [sandbox, security, landlock, push-denial]
model: 
kind: findings
status: todo
outcome: adopted
summary: Measured feasibility of OS-level push denial via Landlock ABI4 network rules: two-sided denial proven, but rules are port-only with no address field
consumed-by: [x2dwu5]
priority: low
---

# Landlock network rules as a push-denial boundary: measured feasibility

Authored while graduating backlog `oq05nc` ("Decide whether to build OS-level push-denial
enforcement, the only non-evadable route to a real no-push boundary"). Every number below was
PRODUCED BY RUNNING CODE on the development host, not read from documentation, because that is the
standard `host_sandbox_profile` already holds itself to and because the whole area exists to refuse
inferred capability claims.

## Why this was measured at all

Backlog `oq05nc` asks whether to build the one mechanism plan `4h7tt0` identified as the only
candidate without a concrete agent-level evasion: kernel-level refusal. `4h7tt0`'s E-02 candidate
table recorded OS-level enforcement as the sole row with "No agent-level evasion", but it also
recorded the cost note that a real boundary "needs a per-host proven sandbox rung plus a network
partition the ladder does not currently implement".

That parenthetical is the entire question, and nobody had measured it. The candidate table was
written as an argument for RETIREMENT, so it never had to establish whether the network partition
was buildable at all - only that it was out of scope for that plan. So the honest state before this
document was: we had a decision to retire, a named direction, and zero evidence about whether the
direction is reachable on any host we run on.

## Host the measurements were taken on

| Property | Value | How established |
|---|---|---|
| Kernel | `6.8.0-142-generic` | `uname -r` |
| Landlock ABI | `4` | `syscall(444, NULL, 0, 1)` (`LANDLOCK_CREATE_RULESET_VERSION`) |
| `bwrap` | present, `/usr/bin/bwrap` | `which bwrap` |
| `unshare` | present, `/usr/bin/unshare` | `which unshare` |
| `slirp4netns` | present, `/usr/bin/slirp4netns` | `which slirp4netns` |
| User namespaces | UNAVAILABLE | `unshare -Urn --map-root-user true` -> `write failed /proc/self/uid_map: Operation not permitted` |

The last row matters and is the same condition `host_sandbox_profile`'s module docstring records:
this host is itself inside a namespace whose `uid_map` denies nested mapping. So `bwrap` and
`unshare` being INSTALLED proves nothing, which is exactly the measured counterexample that made
the sandbox probes attempt-not-inspect. Any push-denial probe inherits that rule without argument.

## Finding 1: Landlock ABI 4 network denial WORKS, two-sided

Landlock gained `handled_access_net` with `LANDLOCK_ACCESS_NET_CONNECT_TCP` at ABI 4, and this host
reports ABI 4. Measured with a ruleset handling `CONNECT_TCP`, one `LANDLOCK_RULE_NET_PORT` rule
allowing a loopback listener's port, then `prctl(PR_SET_NO_NEW_PRIVS)` plus `restrict_self`:

```text
abi: 4
allowed loopback port: 49509
create_ruleset fd: 4 errno: 0
add_rule(NET_PORT) rc: 0 errno: 0
restrict_self rc: 0 errno: 0
allowed connect ok: True 
denied connect refused: True PermissionError(13, 'Permission denied')
RESULT: ENFORCED
```

This clears the bar the existing probes are held to, which is deliberately not "the launcher exited
0". `_denial_checker_source` requires a jail to prove a DENIAL while still permitting the allowed
operation, because a misconfigured permissive jail starts perfectly cleanly and enforces nothing.
The run above satisfies both sides: the allowed connect SUCCEEDED and the port-443 connect was
refused by the kernel with `EPERM`.

So the answer to "is kernel-level network denial reachable here" is YES, and it is reachable with no
new dependency, no helper binary, and no user namespace - which is decisive, because the userns rung
is unavailable on this very host.

## Finding 2: one ruleset carries BOTH filesystem and network rules

This decides whether the existing bootstrap extends in place or a second restriction is needed.
Measured with `handled_access_fs = (1<<15)-1` AND `handled_access_net = CONNECT_TCP` in a single
`landlock_ruleset_attr`, one `PATH_BENEATH` rule, and no net rule at all:

```text
combined create_ruleset fd: 3 errno: 0
add PATH_BENEATH rc: 0
restrict rc: 0
fs allowed write: OK
fs denied write: EPERM -> ENFORCED
net 443: EPERM -> ENFORCED
```

Both classes enforce from one ruleset and one `restrict_self`. `landlock_bootstrap_source`
(`agent_workflows/host_sandbox_profile.py:275`) already packs `handled_access_fs` as the first
member of `struct.pack("=QQ", ALL, 0)` and passes literal `0` as the second - which IS
`handled_access_net`. The network half of the struct is already present and already zero, so
extending it is a change to one packed value plus an added rule loop, not a new mechanism.

Note the fail-closed default this implies: handling `CONNECT_TCP` while adding NO net rule denies
ALL TCP connects. Denial is the default and each allowed port is an explicit opt-in.

## Finding 3 (THE LIMIT): net rules are PORT-ONLY, with no address field

This is the finding that bounds what may honestly be claimed, and it is why this document exists
rather than a one-line "yes it works". `landlock_net_port_attr` is `{allowed_access, port}` and
carries NO address. Measured by allowing port 443 and then connecting to three destinations:

```text
add_rule rc: 0
net_port rule struct size: 16 (allowed_access u64 + port u64; NO address field)
restrict rc: 0
github.com:443 (push-capable): CONNECTED (allowed by the port rule)
cloudflare:443 (unrelated host, SAME port): CONNECTED (allowed by the port rule)
github.com:22 (ssh push, other port): EPERM -> KERNEL DENIED
```

A port rule cannot distinguish a model API endpoint from a git remote, because both are TCP 443.
The consequence is concrete and is the crux of the whole design:

**The agent process needs TCP 443 to reach the model API. A git push over HTTPS also uses TCP 443.
Landlock cannot separate them.** So a Landlock-only partition applied to the agent's own process has
exactly two settings, and neither is the goal:

- allow 443 -> the model works and `git push https://...` ALSO works (no boundary);
- deny 443 -> push is denied and THE AGENT CANNOT RUN AT ALL (no product).

Port 22 denial is real and worth having (it kills SSH-remote push outright), but HTTPS push is the
path that matters, and a port rule does not reach it.

## Finding 4: the architectural consequence, measured against the launch path

`enter_sandbox` wraps the WORKER's argv: `oc_runipd.py:2831` calls `_apply_execution_profile` on the
`argv` that launches the coding agent itself, and that process is the one that talks to the model.
So Finding 3 applies to precisely the process we would need to keep online. A naive "add net rules to
the existing hardened profile" lands on the no-product setting above.

This also sharpens a caveat `4h7tt0` already flagged without measuring: "a sandbox that confines
only the AGENT while the DRIVER retains network could still push on the agent's behalf, so the
boundary must cover the whole turn or it proves less than it claims." The driver must keep network
(it is the same process tree that must fetch and, at release time, legitimately push), so whatever
is built has to state clearly whose network is denied.

Mechanisms that COULD close the 443 gap, none of them measured here and all of them larger than a
probe, so they are recorded as candidates and not as recommendations:

- a network NAMESPACE with a filtering proxy (`slirp4netns` is installed), allowing the model
  endpoint and refusing git remotes by host rather than by port. Blocked on this host today by the
  userns failure above, so it would be a per-host capability like every other rung;
- a DNS/route partition in a namespace, with the same userns dependency;
- confining only a CHILD git process rather than the agent, which is weaker: the agent can invoke
  git however it likes, so the rule has to be inherited to bind, and an inherited 443 denial is
  Finding 3 again.

## What this means for backlog oq05nc's question

The item asks a DECISION question: whether to build. The measured answer is neither a clean yes nor a
clean no, and a plan graduating this item should present it in exactly these three parts:

1. Kernel-level denial is REAL, available at ABI 4, and extends the existing ruleset with no new
   dependency (Findings 1 and 2). The direction `4h7tt0` named is not vapor.
2. It does NOT, by itself, deliver push denial, because the mechanism is port-granular and push
   shares port 443 with the model API (Findings 3 and 4). Anyone who ships "Landlock denies push"
   on the strength of Finding 1 alone would be shipping a fail-OPEN claim, which is the precise
   failure mode this whole area exists to refuse.
3. A complete boundary therefore needs host-granular filtering (namespace plus proxy), which is
   unavailable on this host today and is the `1o4eif`-magnitude project `d07nz2` predicted.

A NARROWER deliverable is available and is worth separating from the big one: deny port 22 and the
non-443 git ports, probe it BY ATTEMPT, and report exactly that - a partial boundary, honestly
labelled, with the 443 hole named in the capability's own note. That is smaller than the full
project and is strictly more than today's zero. It must NOT be called `supports_deny_push`, because
it does not deny push; naming it that would re-create the overclaim `4h7tt0` retired.

## Standing constraints any consumer must not break

- `supports_deny_push` NO LONGER EXISTS. Plan `01reg8` (backlog `aagh7v`) removed the field, the
  `CAP_DENY_PUSH` constant, and three unconsumed action verdicts on the maintainer ruling of
  `4h7tt0` OQ-02. `tests/test_host_capability_extension.py:658` (`DenyPushRemovedTests`) pins the
  absence, so reintroducing the NAME breaks a deliberate guard rather than a stale test.
- Presence inference is FORBIDDEN in writing (`host_sandbox_profile.py` module docstring, the
  `supports_commit_gateway` bullet; and `run_evidence.py:1540-1553` for the retired finding code).
  `slirp4netns` being installed on this host is a perfect example of a signal that proves nothing.
- Spec `25kzda` 4.2 hard-fails `len(RUN_FINDING_CODES) != 12` with `RC-COUNT`
  (`run_evidence.py:1683`), so reintroducing a finding code is a spec amendment plus a shipped
  invariant change, not a row edit.
- Backlog `oq05nc` states the ordering rule: "Only after such a probe exists may a finding code be
  reintroduced in 4.2."

## Reproduction

The three probe scripts were run ad hoc from `/tmp` and are NOT retained in-tree, deliberately: a
throwaway measurement script that nothing calls would rot. The measured behavior is what matters and
it is quoted verbatim above. Any plan acting on this document should re-run the equivalent probe on
the executing host rather than trusting these numbers, because every finding here is host-specific
by construction - which is the whole reason the capability must be PROBED and not declared.
