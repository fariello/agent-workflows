---
id: akmzyq
created: 20261001
set: netnsfilter
order: 00
topic: [sandbox, security, netns, push-denial]
model: 
kind: findings
status: todo
outcome: adopted
summary: Measured feasibility of host-granular egress filtering via network namespace plus filtering proxy: non-evadable boundary proven end to end, contradicting the blocking userns finding in uq4y6q
consumed-by: [m0kl28, nxh5s4, rozdkp, 2j4pd0, wn956n]
priority: low
---

# Host-granular egress filtering via netns plus filtering proxy: measured feasibility

Authored while graduating backlog `sv9ce4` ("Build host-granular outbound network filtering (netns
plus filtering proxy), the only mechanism that can deny a git push without also denying the model
API"). Every number and every quoted command output below was PRODUCED BY RUNNING CODE on the
authoring host, never read from documentation, because that is the standard `host_sandbox_profile`
holds itself to and because this whole area exists to refuse inferred capability claims.

This document exists because the item it graduates rests on a measured premise that DOES NOT
REPRODUCE. Research `uq4y6q` recorded user namespaces as UNAVAILABLE on the measuring host and
therefore treated the netns-plus-proxy direction as blocked and unmeasurable. On this host they are
available, so the direction became measurable, and measuring it changed the plan's shape from
"attempt a mechanism nobody has tried" to "build a mechanism proven end to end, including against
its own teardown".

## Host these measurements were taken on

| Property | Value | How established |
|---|---|---|
| Kernel | `6.8.0-142-generic` | `uname -r` |
| Landlock ABI | `4`, and also `4` INSIDE a netns | `syscall(444, NULL, 0, 1)`, run both outside and inside |
| `unshare` | present, `/usr/bin/unshare` | `which unshare` |
| `bwrap` | present, `/usr/bin/bwrap` | `which bwrap` |
| `slirp4netns` | present, `/usr/bin/slirp4netns` | `which slirp4netns` |
| `iptables` / `nft` | present and USABLE inside the netns | `/usr/sbin/iptables`, `/usr/sbin/nft`; `iptables -t nat -L` succeeded in-ns |
| `capsh` | present | used to drop `CAP_NET_ADMIN` in Finding 6 |
| User namespaces | **AVAILABLE** | `unshare -Urn --map-root-user true` -> rc 0 |

## Finding 0 (THE PREMISE CORRECTION): user namespaces work here

Research `uq4y6q`'s host table records `unshare -Urn --map-root-user true` failing with
`write failed /proc/self/uid_map: Operation not permitted`, and both backlog `sv9ce4` and `wcbpqf`
carry that forward as the reason the netns direction "is blocked on this host today" and is
"per-host capability work". On THIS host the same command succeeds:

```text
unshare -Urn --map-root-user true   ->  rc=0
unshare -Umr true                   ->  rc=0
unshare -Urn --map-root-user ip link show
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
```

The two results are not in conflict and neither is wrong: `uq4y6q` recorded a host that was itself
inside a namespace whose `uid_map` was `0 0 4294967295`, which denies nested mapping. That is
precisely the per-host variability `host_sandbox_profile`'s module docstring documents, and it is why
the capability must be PROBED BY ATTEMPT and never inferred. The correction to draw is NOT "userns is
available" as a general claim; it is that availability VARIES BY HOST, so the mechanism is buildable
and must ship behind an executed probe rather than a presence check.

A caution that follows directly, and that any consumer must preserve: `bwrap`, `unshare` and
`slirp4netns` were all INSTALLED on `uq4y6q`'s host and the namespace still could not be created.
Installation proves nothing. The probe in Finding 7 is therefore two-sided by construction.

## Finding 1: a netns denies ALL egress by default, which is the fail-closed starting point

A fresh network namespace has only a down `lo` and no route, so nothing reaches the network:

```text
unshare -Urn --map-root-user python3 -c "connect(('1.1.1.1',443))"
  -> OSError [Errno 101] Network is unreachable
```

Denial is the DEFAULT and every allowed destination is an explicit opt-in. This is the opposite
posture from the Landlock port rules of `uq4y6q` Finding 3, where the operator chooses ports to
allow and everything unnamed stays reachable. It is also the posture this repository's sandbox work
already prefers: fail closed, then open precisely what the product needs.

`bwrap` reaches the same state by a different route, which matters because it is an existing rung in
`_SANDBOX_LADDER`:

```text
bwrap --unshare-net --ro-bind / / --dev /dev python3 -c "connect(('1.1.1.1',443))"
  -> OSError [Errno 101] Network is unreachable
```

## Finding 2: an AF_UNIX socket crosses the netns boundary, so the proxy needs no IP connectivity

This is the finding that makes the design simple, and it is the one most likely to be got wrong by
reasoning instead of measuring. A network namespace partitions NETWORK interfaces, not the
filesystem, so a unix-domain socket created by the parent is reachable from inside the child's netns:

```text
unix socket across netns: PARENT-PROXY-REACHED
direct outbound from netns: OSError [Errno 101] Network is unreachable
child rc: 0  parent received: b'HELLO-FROM-NETNS'
```

Both halves in one run: the control channel to the parent WORKS while the child's own egress stays
denied. The consequence is that the broker needs no veth pair, no bridge, no NAT and no
`slirp4netns` at all. Measured separately, a loopback relay inside the netns also works after
`ip link set lo up`, binding and connecting on `127.0.0.1` without `slirp4netns`:

```text
ip link set lo up rc: 0
loopback inside netns: CONNECTED on 57747
```

So `slirp4netns` being installed (the signal `uq4y6q` correctly flagged as proving nothing) is not
merely insufficient, it is UNNECESSARY for this design.

## Finding 3: the boundary separates hosts on the SAME port, which is the whole point

This is what Landlock provably cannot do (`uq4y6q` Finding 3: the rule struct is
`{allowed_access, port}`, 16 bytes, no address field, so `github.com:443` and `1.1.1.1:443` are
indistinguishable). Measured with a CONNECT-filtering broker on the parent side allowing exactly
`api.anthropic.com` and refusing everything else, with the agent inside the netns:

```text
--- DIRECT (no proxy) outbound from netns:
  github direct: OSError [Errno 101] Network is unreachable
--- VIA PROXY, denied host (github.com):
  rc: 56 out: 000 err: curl: (56) CONNECT tunnel failed, response 403
--- VIA PROXY, allowed host (api.anthropic.com):
  rc: 0 out: 404
--- GIT PUSH attempt via proxy (denied remote):
  git rc: 128 err: fatal: unable to access 'https://github.com/fariello/agent-workflows/':
          CONNECT tunnel failed, response 403
```

Broker-side log for the same run:

```text
PROXY DENIED github.com
PROXY ALLOWED api.anthropic.com
PROXY DENIED github.com
```

Both destinations are TCP 443. One is allowed and the other refused, and a real `git` invocation
against a real remote failed with `rc 128`. That is the exact partition the Landlock mechanism cannot
express and the reason this item exists. The `404` on the allowed host is the endpoint's own answer
to an unauthenticated `GET`, which is a SUCCESSFUL tunnel: the proof is `rc: 0` with a response code
at all, versus `rc: 56` and `000` when the tunnel was refused.

## Finding 4: five evasion attempts, all held

A boundary is only worth the name if it survives an agent that does not cooperate. Each row was run
from inside the netns:

| # | Evasion attempted | Measured result |
|---|---|---|
| 1 | Unset every proxy env var and push directly | `git rc: 128`, `Could not resolve host: github.com` |
| 2 | `CONNECT` to GitHub by raw IP, bypassing DNS | `rc: 56`, `CONNECT tunnel failed, response 403`; broker logged `PROXY DENIED 140.82.113.4:443` |
| 3 | SSH push path (port 22) through the broker | `rc: 56`, `403`; broker logged `PROXY DENIED github.com:22` |
| 4 | Re-`unshare` a fresh netns to escape | `OSError [Errno 101] Network is unreachable` |
| 5 | Allowed host must still work (the product must survive) | `rc: 0`, code `404` |

Row 1 is the important one and is worth stating plainly: because the netns has NO route, an agent
that ignores `HTTPS_PROXY` entirely does not get a bypass, it gets no network. Row 4 is the
"escape upward" attempt and fails for the same reason: a nested namespace inherits no route either.
Row 5 is what separates this from the Landlock dead end, where denying 443 denied the product too.

## Finding 5: transparent interception is available, so the boundary need not rely on env vars

Findings 3 and 4 use a broker the client is CONFIGURED to use. That is sufficient given Finding 4
row 1 (an unconfigured client simply has no network), but a REDIRECT rule is strictly stronger
because the intended destination is recovered even from a hostile client. Measured inside the netns,
with a dummy device supplying a route so the nat table is reached while nothing can actually egress:

```text
default route via dummy0 installed
-A OUTPUT -p tcp -m tcp --dport 443 -j REDIRECT --to-ports 9999
hostile raw connect to github:443 -> INTERCEPTED
intended destinations recovered by interceptor: ['140.82.113.4:443']
```

The hostile client used a raw socket with no proxy configuration and was still intercepted, and
`SO_ORIGINAL_DST` recovered `140.82.113.4:443`, so a policy decision can be made on the destination
the agent actually intended. This is what makes the mechanism a boundary rather than a convention.

## Finding 6 (THE DESIGN CONSTRAINT): the agent must not hold CAP_NET_ADMIN

The naive arrangement is EVADABLE and must not be built. An agent placed in a netns it created is
root in that namespace and can simply delete the rules that confine it:

```text
=== as the confined agent, try to tear the boundary down:
  FLUSH SUCCEEDED -> boundary is EVADABLE
-P OUTPUT ACCEPT
```

The correct arrangement has the PARENT create the namespace and install the policy while privileged
in it, then hand off to the agent WITHOUT `CAP_NET_ADMIN`. Measured, including the authoritative
post-attempt check from the parent's side:

```text
[parent] boundary installed. Verifying it is present:
-A OUTPUT -p tcp -m tcp --dport 443 -j REDIRECT --to-ports 9999
[parent] dropping CAP_NET_ADMIN, handing off to agent payload:
[agent] flush rc=4 out=iptables v1.8.10 (nf_tables): Could not fetch rule set generation id:
        Permission denied (you must be root)
[agent] VERDICT: boundary HELD (flush refused)
[parent] boundary AFTER the agent attempt (authoritative check):
-A OUTPUT -p tcp -m tcp --dport 443 -j REDIRECT --to-ports 9999
```

The rule is intact after the attempt, verified by the parent rather than by the process that tried to
remove it. Two lessons, both of which a plan must carry: capability dropping is LOAD-BEARING and not
hygiene, and a teardown attempt must be verified from OUTSIDE the sandbox, because asking the
confined process whether it is still confined is not evidence.

A methodology note worth preserving, since it nearly produced a false pass here: the first version of
this measurement piped `iptables` through `head`, so the pipeline's exit status masked the real one
and the test printed `FLUSH SUCCEEDED` for a flush that had actually been REFUSED. A probe that
reports the wrong answer in the SAFE direction is still a broken probe, and this one would have
argued against building a mechanism that works.

## Finding 7: a hermetic two-sided probe is cheap and needs no external network

The capability must be probed BY ATTEMPT, like every other rung. A hermetic probe is available: the
parent holds a TCP listener standing in for a denied remote, plus an AF_UNIX broker standing in for
the allowed channel, and the child must FAIL to reach the first while SUCCEEDING at the second.
Measured, three consecutive runs:

```text
{'denied_side': 'refused: OSError: [Errno 101] Network is unreachable',
 'allowed_side': 'BROKER-REACHED'}
probe rc: 0 (0=two-sided proven, 3=jail too tight, 4=not enforced)
```

Five timed runs: `0.079s`, `0.090s`, `0.040s`, `0.040s`, `0.036s`. For comparison a warm
`detect_host_capabilities('opencode')` measured `0.052s` on the same host, so a probe in this shape
roughly doubles that call. Whether that cost is acceptable depends on where the probe is registered
(the runner-safety group is deliberately uncached), which is a decision a plan must make explicitly
rather than inherit.

Three properties make this probe shape the right one: it needs NO external network, so it is
hermetic and CI-safe; it distinguishes the three outcomes the existing `_denial_checker_source`
distinguishes, so "jail too tight" cannot be reported as success; and it would return False on a host
where the namespace cannot be created, which is the `uq4y6q` host, fail-closed and correctly.

## What this means for backlog sv9ce4

The item is buildable, and more of it is proven than the item assumes. Specifically:

1. The mechanism works END TO END and does the one thing Landlock cannot: it separates a git remote
   from the model API on the same port (Finding 3), including against a real `git` invocation.
2. It is a BOUNDARY, not a convention, provided the agent does not hold `CAP_NET_ADMIN` (Finding 6).
   That constraint is the single most important thing for an implementation to get right, and the
   naive version is evadable in one command.
3. It needs NO new dependency: no `slirp4netns`, no veth, no NAT, no bridge (Finding 2).
4. It is PER-HOST capability work, exactly as the item says, because namespace creation genuinely
   fails on some hosts (Finding 0). The probe must be two-sided and executed (Finding 7).

What is NOT established here, and must not be inferred from this document:

- Nothing above integrates with `oc_runipd._apply_execution_profile`, `build_sandbox_plan` or
  `enter_sandbox`. These were standalone measurements; the integration is unwritten work.
- The ALLOW LIST is policy, not measurement. These runs hardcoded `api.anthropic.com` to prove the
  partition is expressible. Which endpoints a real profile permits (and how a model endpoint is
  discovered rather than assumed) is an open design question.
- No claim is made that this denies EVERY push route. A proxy that allows a host also allows
  everything reachable at that host, and a model endpoint that proxies arbitrary traffic would be a
  hole. The honest claim is destination-granular filtering with a declared allow list, not a
  universal push boundary.
- The macOS and non-Linux story is untouched. Every measurement here is Linux namespace behavior.

## Standing constraints any consumer must not break

- Presence inference remains FORBIDDEN in writing (`host_sandbox_profile`'s module docstring on
  `supports_commit_gateway`; `run_evidence`'s `RUN-NO-PUSH` retirement comment). Finding 0 is a
  direct demonstration of why: three relevant binaries were installed on `uq4y6q`'s host and the
  namespace still could not be created. A capability here must be set True only by an executed
  two-sided probe.
- `supports_deny_push` MUST NOT be reintroduced as a name. Plan `01reg8` removed the field and
  `CAP_DENY_PUSH`, and `tests/test_host_capability_extension.py`'s `DenyPushRemovedTests` pins the
  absence, so reusing the name breaks a deliberate guard. Nothing in this document justifies a claim
  that broad; see the "what is NOT established" list.
- `run_evidence.validate_finding_table` hard-fails a code count other than 12 with `RC-COUNT`, so
  reintroducing a finding code is a spec amendment plus a shipped invariant change, never a row edit.
  Backlog `oq05nc`'s ordering rule still governs: a probe must exist before a code returns.
- Do NOT bind any claim to the presence of a proxy, a namespace tool, or a config flag. That is
  forbidden in writing in two modules and would convert today's safe fail-closed state into a
  fail-OPEN checker.

## Reproduction

The probe scripts were run ad hoc and are NOT retained in-tree, deliberately, matching `uq4y6q`'s
reasoning: a throwaway measurement script nothing calls would rot. Every result is quoted verbatim
above, and each is reproducible from the description given with it. Any plan acting on this document
MUST re-run the equivalent probe on the executing host rather than trusting these numbers, because
Finding 0 is itself a measurement of how much these results vary BY HOST.
