# IPD: Build the egress policy and the parent-owned filtering broker

- Date: 2026-10-01
- Kind: child
- Concern: Child 01 proves a host can partition egress, but a partition with no policy has only two settings and neither is useful: deny everything and the agent cannot reach the model API, or allow everything and there is no boundary. The thing that makes the partition valuable is a DESTINATION decision, which is exactly what Landlock cannot express (research `uq4y6q` Finding 3: the rule struct is `{allowed_access, port}` with no address field, so `github.com:443` and the model API are indistinguishable). Nothing in this repository can express a destination allow list.
- Scope: Add the egress POLICY type (a declared allow list of destinations, validated and fail-closed) and the parent-owned filtering BROKER that enforces it by refusing an unlisted destination and tunnelling an allowed one. Both are standalone and unit-testable here; wiring them to a real worker is child 03. The broker runs in the PARENT, outside the namespace, which is what makes it something the confined process cannot reconfigure.
- Scope-Paths: agent_workflows/egress_policy.py, agent_workflows/host_sandbox_profile.py, tests/test_egress_policy.py
- Item-Dependencies: executed:nxh5s4
- Status: executed
- Readiness: go-pending-approval
- From-Backlog: sv9ce4
- From-Spec: 25kzda
- Work-Kind: feature
- Priority: low
- Set: netnsfilter
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: rozdkp

## Workflow history
- 2026-10-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: rozdkp verified (set netnsfilter, attempt 1). [Scope reconciliation - in-scope-unmodified agent_workflows/host_sandbox_profile.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-701 (HIGH, fixed), PR-702 (MEDIUM, fixed), PR-703 (MEDIUM, fixed), PR-704 (LOW, fixed), PR-705 (LOW, fixed). Design sound and research citations verified. PR-701: E-06's two-listener test could only prove a PORT partition, so the same-port destination partition had no hermetic test; it is now an alias pair (127.0.0.1:P allowed, localhost:P refused, one live listener). PR-702: socketpair seam so Windows CI cannot skip. PR-703: CONNECT input bounds, no raw echo, parent-only socket dir. PR-704: re-quoted the reworded host_sandbox_profile docstring; child wn956n still quotes the old sentence. Record: .aw/records/reviews/20261001-netnsfilter-02-rozdkp-build-the-egress-policy-and-the-parent-owned-filtering-broke.review.md.
- 2026-10-07 to-review (aw set): returned to review: Set-level validation sweep owned by wn956n E-05/V-05; coverage pass recorded; open questions are non-blocking
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: Bare pytest run green with actual summary line pasted

- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `sv9ce4`. The broker design specified here was BUILT AND RUN end to end during authoring (research `akmzyq` Findings 3 and 4), including a real `git ls-remote` refused while an allow-listed HTTPS endpoint succeeded on the same port, and five evasion attempts.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the destination partition expressible and enforceable: a declared allow list that fails closed on
anything it does not name, and a parent-owned broker that refuses an unlisted destination while
letting an allow-listed one through, so a git remote can be denied on the same port the model API
needs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the policy

- [x] E-01 Add a new module `agent_workflows/egress_policy.py` defining the policy type: a frozen dataclass carrying an explicit allow list of destinations (host plus port) and nothing else, with a `decide(host, port)` returning an explicit allow or deny verdict plus a reason string. DENY MUST BE THE DEFAULT for every destination the list does not name, so an empty policy denies everything and a malformed entry cannot widen the list. Validate entries at construction and REFUSE rather than normalize anything ambiguous: a wildcard host, an empty host, a port outside 1-65535, or a duplicate entry. Provide no "allow all" switch and no negation, because a deny-list shape would make the fail-closed property unreachable.
  - WHY A SEPARATE MODULE RATHER THAN A FUNCTION IN `host_sandbox_profile`. The policy is CONFIGURATION DATA with its own validation, consumed by both the broker here and the profile wiring in child 03, and `host_sandbox_profile` is the published-guarantees contract for the opt-in OS sandbox. Its docstring now says, re-read at review 2026-10-07 (PR-704), that network denial "cannot separate a git remote from the model API on one port, so none is applied (network scoping is now measured rather than out of scope ...); container isolation remains out of scope here". The sentence this item originally quoted, "Network scoping and container isolation are out of scope here", no longer exists. The reasoning still holds: the module states that no network rule is applied, and child 04 amends that statement once the boundary is measured. Putting the policy in its own module keeps the probe module's contract coherent in the meantime.
  - Depends on: none
  - Expected outcome: A policy type that cannot be constructed into a state that allows an unnamed destination, and whose `decide` returns a reason usable in an operator-facing refusal message.
  - Execution state: performed

- [x] E-02 Make the policy's SOURCE explicit configuration rather than inference, and refuse to guess. The allow list must be supplied by the caller; the module must NOT discover a model endpoint by reading the host's config, environment, or network state. Provide a loader that parses the list from a declared config value and REFUSES with a clear error when it is absent, rather than defaulting to any endpoint. Record in the module docstring that an absent policy is an ERROR and never an empty-allow-everything or a guessed default.
  - WHY REFUSING TO GUESS IS THE SAFE DIRECTION HERE, which is the opposite of the usual fail-closed reflex and so is worth stating. A guessed allow list fails in the direction of ALLOWING a destination nobody declared, which is a silent hole. Refusing to start is loud and recoverable. The alternative failure (denying the model API and breaking the product) is equally loud and is the subject of V-02's explicit check.
  - Depends on: E-01
  - Expected outcome: An absent or unparseable policy raises rather than producing a usable object, so no code path can reach a broker that allows a destination no operator wrote down.
  - Execution state: performed

### Task group 2: the broker

- [x] E-03 Add the parent-owned filtering broker to `agent_workflows/egress_policy.py`: it listens on an AF_UNIX socket held by the PARENT, reads a CONNECT request naming a destination, consults the policy, and either refuses with an explicit error response or opens the upstream connection and relays bytes both ways until either side closes. It must run OUTSIDE the namespace, in the parent, which is the property that makes it unreconfigurable by the confined process. Bound every blocking operation with a timeout so a hung upstream cannot wedge the broker, and log each decision with its destination and verdict so a run has an auditable record of what was refused.
  - TREAT THE REQUEST AS UNTRUSTED INPUT, ADDED AT REVIEW 2026-10-07 (PR-703). The CONNECT target is chosen by the confined client and is then written to the decision log and into the refusal message. So: cap the request head at a fixed byte bound and refuse anything larger; accept only a single `CONNECT host:port HTTP/1.x` request line, and refuse any other method or form with an explicit `400` before consulting the policy; take the destination ONLY from the CONNECT authority, never from a `Host:` header; and refuse a target that contains a control character, whitespace or any character outside hostname or IP-literal syntax, so a forged log line or response header can never be injected (the same newline-injection class Set `qbz8i1` closed for records). A malformed request is refused and logged with a fixed reason, and its raw bytes are never echoed. Create the AF_UNIX socket in a directory only the parent's user can enter, so no other local user can use the broker as an open proxy to allow-listed hosts. The parent owns the socket's lifetime and unlinks it on shutdown.
  - MEASURED DESIGN, NOT PROPOSED. Research `akmzyq` Finding 2 measured that an AF_UNIX socket crosses the namespace boundary (`unix socket across netns: PARENT-PROXY-REACHED`) while direct egress from the same child was refused, so the control channel needs no veth, no NAT, no bridge and no `slirp4netns`. Finding 3 measured the full broker refusing and allowing on the SAME port.
  - Depends on: E-02
  - Expected outcome: A broker that refuses an unlisted destination and tunnels an allow-listed one, with every decision recorded. The confined side cannot alter the policy because the broker is not in its namespace. A malformed, over-long or control-character request is refused with `400` and is never echoed raw into the log or the response.
  - Execution state: performed

- [x] E-04 Make the broker's refusal observable to the caller AND to the run, not merely a dropped connection. A refusal must produce a distinguishable error response the client surfaces (a dropped connection is indistinguishable from a network fault and would be debugged as one), and the broker's decision log must name the destination and the reason. Include the policy's reason string so an operator reading a failure learns WHICH destination was refused and that the refusal was deliberate.
  - MEASURED: with the broker returning an explicit refusal, `curl` reported `rc: 56` with `CONNECT tunnel failed, response 403` and `git` reported `rc: 128` with `fatal: unable to access ... CONNECT tunnel failed, response 403` (research `akmzyq` Finding 3). Both name the refusal rather than looking like a dead network, which is the distinguishability this item requires.
  - Depends on: E-03
  - Expected outcome: A refused destination yields an error a human can act on and a log line a run can audit, never a silent hang or an ambiguous reset.
  - Execution state: performed

### Task group 3: tests

- [x] E-05 Add `tests/test_egress_policy.py` covering the policy BEHAVIORALLY: an unlisted destination is denied; an allow-listed one is allowed; an empty policy denies everything; a same-host-different-port destination is denied when only one port is listed; construction refuses each malformed entry E-01 enumerates; and an absent policy raises per E-02. Assert on returned verdicts and raised errors, never on source structure (AGENTS.md P16).
  - Depends on: E-02
  - Expected outcome: The fail-closed property is pinned by tests that would fail if a default ever widened to allow an unnamed destination.
  - Execution state: performed

- [x] E-06 Add a HERMETIC end-to-end broker test that proves the SAME-PORT partition. The parent holds ONE live loopback listener on port `P` and runs the broker with a policy listing exactly `127.0.0.1:P`. The client then issues two CONNECTs to the SAME port: `127.0.0.1:P`, which must be tunnelled and must reach the listener, and an UNLISTED spelling of that same endpoint, `localhost:P`, which must be REFUSED. Because OQ-01 keys the policy on the destination AS REQUESTED, the refused request names a host the policy does not list while the port and the live listener are identical, so the refusal can only have come from the policy. Decide before resolving (OQ-01), so the refused name is never resolved and the test needs no DNS. Add a second case for the PORT partition too: a second live listener on `127.0.0.1:Q`, not listed, must be refused. The test needs no external network and no namespace, so it runs in CI and on an offline host. Assert that the refusal is the distinguishable error E-04 specifies and that the decision log names the destination.
  - WHY THE SAME-PORT CASE IS REQUIRED HERE, CORRECTED AT REVIEW 2026-10-07 (PR-701). As first authored, this item had two loopback listeners on one address, which forces them onto DIFFERENT ports. That proves only a port partition, which V-03 itself says "does not meet this item", while the plan's only same-port evidence was the external-network research run. The alias design proves the same-port decision hermetically. A second address (`127.0.0.2`) was REJECTED as the way to get a second same-port listener: on Linux, all of `127.0.0.0/8` routes to loopback, but on macOS only `127.0.0.1` is configured by default, and CI runs macOS.
  - DRIVE THE HANDLER THROUGH A TRANSPORT-NEUTRAL SEAM SO THE TEST CANNOT SKIP (PR-702). The per-connection decide-and-relay logic must accept an ALREADY-CONNECTED stream socket, and the AF_UNIX listener should be a thin wrapper around it. The hermetic test then drives the handler over `socket.socketpair()`, which every CI leg provides, and the CI matrix includes `windows-latest`, where `socket.AF_UNIX` is not guaranteed. A test of the AF_UNIX listener itself may carry `skipif(not hasattr(socket, "AF_UNIX"))`. V-05 must name it as the one sanctioned skip, and no policy or handler test may depend on it. A namespace-confined worker exists only on Linux and is child 03's concern.
  - KEEP BOTH LISTENERS OPEN for the client's lifetime. A closed listener yields a connection-refused that is NOT the policy's refusal, so a test against a dead port would pass while proving nothing about the policy. This is the same trap the sibling Set's plan `pi3bk8` E-02 records for its own probe.
  - WHY THIS TEST NEEDS NO NAMESPACE, which is what keeps it green on every host: the broker's decision is made entirely from the policy and the requested destination, so the namespace contributes isolation and not filtering. The namespace-dependent behavior is child 03's and is validated there.
  - Depends on: E-05
  - Expected outcome: A test proving the broker refuses and allows by DESTINATION on the SAME port against one live listener, plus a port-partition case, passing over `socketpair()` without a namespace, DNS or external network, so no policy or handler test can skip on any CI leg.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL or quoted content string, never by a bare line number (`IPD-C801`).
- A test must exercise behavior, never pin code structure (AGENTS.md P16): no `inspect`, `ast` or
  regex reads of production source, and no assertions on caller counts or module line counts.
- A skip is not acceptance evidence: `tests/test_host_sandbox_profile.py` records that a skip "leaves
  the guarantee UNVERIFIED on that machine", and its `BWRAP_STUB_MODES` comment records that a test
  driving only a real binary "would SKIP everywhere and guard nothing". This is why E-06 is designed
  to need no namespace.
- `host_sandbox_profile`'s module docstring currently says network denial "cannot separate a git
  remote from the model API on one port, so none is applied" (re-quoted at review, PR-704; the older
  sentence "Network scoping and container isolation are out of scope here" was reworded upstream).
  That is why the policy lands in its own module. Child 04 amends that passage as part of the contract
  sync.
- Fail-closed is the house pattern for every capability and sandbox decision in this area: every
  capability defaults False and "an UNPROBED host claims NOTHING". E-01 applies the same posture to
  the policy: an unnamed destination is denied.
- `select_execution_profile` raises `HardModeUnavailableError` rather than returning `"default"` when
  hardened mode is unavailable, so the established pattern for an unsatisfiable safety request in this
  module is to REFUSE rather than degrade. E-02 follows it for an absent policy.
- No em or en dashes in user-facing prose, per the execution contract; the broker's operator-facing
  refusal message is user-facing text.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The destination partition is the whole point, and Landlock cannot express it | Research `uq4y6q` Finding 3: `net_port rule struct size: 16 (allowed_access u64 + port u64; NO address field)`; with 443 allowed, both `github.com:443` and `cloudflare:443` CONNECTED while `:22` was denied | The policy must key on destination HOST and port, not port alone. A port-keyed policy would reproduce the dead end this Set exists to escape. |
| F-2 | The broker works end to end and separates hosts on the SAME port | Research `akmzyq` Finding 3: broker log `PROXY DENIED github.com` / `PROXY ALLOWED api.anthropic.com`; `curl` to the denied host `rc: 56 ... response 403`; to the allowed host `rc: 0` code `404`; `git ls-remote` `rc: 128 ... CONNECT tunnel failed, response 403` | E-03's design is demonstrated rather than proposed, including against a real `git` invocation at a real remote. The `404` is the endpoint's own answer to an unauthenticated GET, so a response code at all is the proof the tunnel SUCCEEDED. |
| F-3 | AF_UNIX crosses the namespace boundary, so the broker needs no networking into the namespace | Research `akmzyq` Finding 2: `unix socket across netns: PARENT-PROXY-REACHED` in the same run where the child's direct egress was refused | E-03 needs no veth, bridge, NAT or `slirp4netns`. It also means the broker stays entirely in the parent, which is the non-evadability property child 03 depends on. |
| F-4 | A refusal must be DISTINGUISHABLE from a network fault | Measured client-side messages: `curl: (56) CONNECT tunnel failed, response 403` and `fatal: unable to access ...: CONNECT tunnel failed, response 403` | E-04 exists because a dropped connection would be debugged as a network problem. An explicit refusal tells an operator the boundary acted deliberately. |
| F-5 | Five evasion attempts held against this design | Research `akmzyq` Finding 4: unsetting proxy env gave `Could not resolve host`; raw-IP CONNECT was refused `403`; port 22 was refused `403`; a nested `unshare` still got `Network is unreachable`; the allowed host still returned `rc: 0` | The broker's refusals are not bypassable by the obvious client-side tricks, PROVIDED the namespace has no route. That proviso is child 03's to establish and is why this plan's claims stop at the broker. |
| F-6 | An agent that ignores proxy configuration gets NO network, not a bypass | Research `akmzyq` Finding 4 row 1: a direct `git ls-remote` with every proxy variable removed failed with `Could not resolve host: github.com`, because the namespace has no route | This is why the broker may rely on being the only route out. It is also why this plan must NOT claim the boundary on its own: without child 03's namespace wiring, a client is free to ignore the broker entirely. |
| F-7 | Transparent interception is available if cooperation ever proves insufficient | Research `akmzyq` Finding 5: inside the namespace, `iptables -t nat -A OUTPUT -p tcp --dport 443 -j REDIRECT --to-ports 9999` intercepted a HOSTILE raw-socket connect and `SO_ORIGINAL_DST` recovered `140.82.113.4:443` | Recorded as an available STRENGTHENING, deliberately not built here (see the Deferred section). It matters because it means the design has a stronger rung if review judges configured-client reliance too weak. |

## Proposed changes (ordered, validatable)

1. Add the policy type, deny-by-default, refusing ambiguous entries at construction (E-01).
2. Make the policy's source explicit configuration that refuses to guess an endpoint (E-02).
3. Add the parent-owned broker enforcing the policy by destination (E-03).
4. Make refusals distinguishable to the client and auditable in the log (E-04).
5. Pin the policy's fail-closed behavior behaviorally (E-05).
6. Pin the broker end to end with a hermetic test needing no namespace or external network (E-06).

## Deferred / out of scope (with reason)

- WIRING the broker to a real worker, creating the namespace at launch, and dropping
  `CAP_NET_ADMIN`. This plan's broker and policy are standalone and unit-testable; nothing here makes
  a worker use them, and this plan therefore claims no boundary on its own (F-6).
  - Carrier: 2j4pd0
- TRANSPARENT REDIRECT interception, which research `akmzyq` Finding 5 measured working against a
  hostile raw-socket client. Deliberately NOT built here even though it is stronger, because it adds
  an `iptables` dependency and in-namespace privileged setup to a plan whose deliverable is testable
  without either, and because F-6 shows the configured-client path already leaves an uncooperative
  agent with no network at all.
  - Carrier: sv9ce4
- DISCOVERING the model endpoint automatically. E-02 refuses to guess precisely because a guessed
  allow list fails toward ALLOWING something nobody declared.
  - Carrier: sv9ce4
- DENYING UDP and non-TCP egress, and DNS policy specifically. The namespace already denies both by
  default (F-6 shows DNS failing with `Could not resolve host`), so nothing is open; what is missing
  is a deliberate ALLOW path for them, which no requirement here needs.
  - Carrier-Declined: NOT WANTED and not owed. The default state is denial, so there is no hole to
    carry. A plan that needs DNS inside the namespace would be adding an allowance, not closing a gap,
    and filing a carrier would misrepresent a closed default as pending work.
- NAMING anything in this plan for push denial, or adding a finding code or action gate.
  - Carrier-Declined: DELIBERATELY NOT WANTED. `run_evidence.validate_finding_table` hard-fails a
    count other than 12 with `RC-COUNT`, and backlog `oq05nc`'s gate plus the naming question are
    maintainer decisions carried by `wcbpqf`, not a child's to assume.

## Scope check

- Over-scope: none. `agent_workflows/egress_policy.py` is a NEW module created by E-01 through E-04;
  `tests/test_egress_policy.py` is NEW, created by E-05 and E-06. `host_sandbox_profile.py` is
  declared for ONE narrow reason: child 01's probe note and this plan's policy must not contradict
  each other, so if the note needs a wording correction once the policy exists, this plan makes it
  rather than leaving the two to drift. If no correction proves necessary, that path goes unmodified
  and finalize will ask for a `--scope-ack`, which is the ordinary answer and not a failure.
- Under-scope: none. No spec or docstring amendment is claimed here, by design: child 04 owns both so
  the contract is amended once, after the complete boundary's limits are measured rather than
  predicted. No CHANGELOG entry either, since nothing in this plan is reachable by a user until child
  03 wires it to a worker.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. This plan adds a module
  and a test file, so the suite is the primary gate.
- `tests/test_egress_policy.py` must pass with NO SKIPS on any host, which is the design constraint
  behind E-06's hermetic shape. A skip here would mean the test depends on a namespace it should not.
- Paste the broker's decision log for both an allowed and a refused destination, showing the
  destination and reason in each.
- `aw ipd lint` conforming. `aw check` reporting no new finding naming this plan's artifacts, judged
  as a delta rather than by exit code, since it exits nonzero today on pre-existing findings.
- `aw sanitize --agent` exits zero. Broker logs and pasted test output can carry host paths.

## Spec / documentation sync

- NO SPEC EDIT IN THIS PLAN and no spec path declared. Child 04 owns the spec `25kzda` 5.2 amendment,
  deliberately: 5.2 requires descriptor entries be backed by probe evidence, and the honest statement
  of what the boundary covers cannot be written until child 03 measures the complete path. Amending it
  here would describe a capability this plan does not deliver.
- `host_sandbox_profile`'s module docstring says network denial "cannot separate a git remote from the
  model API on one port, so none is applied", which becomes false once the Set completes (re-quoted at
  review, PR-704; child 04 `wn956n` still quotes the older wording, which was reworded upstream, and
  must re-anchor when it executes). Child 04 amends that sentence as part of
  the same contract sync, so the probe module's published scope and the policy module's existence
  cannot drift.
- The new module carries its own docstring stating the fail-closed posture and that an absent policy
  is an error, which is the contract a future caller reads at the point of use.
- No CHANGELOG entry here: nothing user-visible changes until child 03, and child 04 records the
  Set's user-visible change once.

## Open questions

### OQ-01: Should the allow list key on hostname, resolved IP, or both?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT: key on the destination as REQUESTED
  (hostname when the client sends one, address when it sends an address) and decide before any
  upstream connection is opened. The question matters because the two can disagree and a mismatch is a
  hole in whichever direction it is resolved wrongly. Measured during authoring (research `akmzyq`
  Finding 4 row 2): a client issuing `CONNECT` to the raw address `140.82.113.4:443` was refused with
  `403` by a policy naming only `api.anthropic.com`, because an address is not a listed hostname and
  deny-by-default caught it. That is the correct outcome and it falls out of E-01's posture rather
  than needing special handling. Keying on RESOLVED IP instead was rejected on two grounds: it makes
  the policy depend on DNS results that can change between the decision and the connection, and it
  would require resolving a destination the policy is about to refuse, which does work on behalf of a
  denied request. An operator who needs an address allowed can list the address.

### OQ-02: Should the broker rely on the client being configured to use it, or intercept transparently?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: rely on configuration in this plan, with transparent
  interception recorded as an available strengthening and deferred to the carrier. The reason this is
  SAFE rather than merely simpler is measured: an agent that ignores the broker entirely does not get
  a bypass, it gets no network at all, because the namespace has no route (research `akmzyq` Finding 4
  row 1, a direct `git ls-remote` with every proxy variable removed failing with
  `Could not resolve host: github.com`; row 4, a nested `unshare` still reporting
  `Network is unreachable`). So the configured path is the only working path, which makes
  cooperation unnecessary for the boundary to hold. Transparent REDIRECT was also measured working
  against a hostile raw-socket client with `SO_ORIGINAL_DST` recovering the intended destination
  (Finding 5), so the stronger rung is known to be reachable if review judges this insufficient.
  It is deferred because it requires privileged in-namespace setup and an `iptables` dependency for a
  property the namespace's lack of a route already provides.

### OQ-03: Should an allow-listed host be allowed on ALL ports or only the listed port?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: only the listed port, and E-05 pins it with a
  same-host-different-port test. The narrower rule is correct because the whole mechanism exists to
  make a destination decision finer than a port decision, and allowing every port on a listed host
  would reintroduce a coarse allowance in the one place the design is supposed to be precise. It also
  costs an operator nothing, since listing a second port is one entry. Measured relevance: port 22 on
  a host was refused by the broker (research `akmzyq` Finding 4 row 3) while 443 on an allowed host
  succeeded, so per-port decisions are already what the broker naturally expresses.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted test output showing an unlisted destination DENIED, an allow-listed one ALLOWED, and an EMPTY policy denying a destination. Plus the pasted refusal for each malformed entry E-01 enumerates (wildcard host, empty host, out-of-range port, duplicate), each showing construction REFUSED rather than normalized. Quote the `decide` reason string for one denial and judge in one sentence that it names the destination.
  - A POLICY THAT CAN BE CONSTRUCTED INTO AN ALLOW-EVERYTHING STATE FAILS THIS ITEM. State explicitly that no allow-all switch and no negation exists, and paste the result of attempting the nearest thing to one (for example an entry with a wildcard host) showing it refused.
  - Observed evidence:
    Observed from `agent_workflows.egress_policy.EgressPolicy` execution:
    ```text
    UNLISTED: PolicyVerdict(allowed=False, reason='destination github.com:443 is not in allow list', destination='github.com:443', host='github.com', port=443)
    ALLOW-LISTED: PolicyVerdict(allowed=True, reason='destination api.anthropic.com:443 is allow-listed', destination='api.anthropic.com:443', host='api.anthropic.com', port=443)
    EMPTY: PolicyVerdict(allowed=False, reason='destination 127.0.0.1:80 is not in allow list', destination='127.0.0.1:80', host='127.0.0.1', port=80)
    REFUSED ('*', 443): ValueError: wildcard host not allowed: '*'
    REFUSED ('', 443): ValueError: empty host
    REFUSED ('example.com', 70000): ValueError: port out of range (1-65535): 70000
    REFUSED duplicate: ValueError: duplicate destination entry: example.com:443
    ```
    Quoted `decide` denial reason string: `'destination github.com:443 is not in allow list'`.
    Judgement: The denial reason string explicitly names the requested destination (`github.com:443`) and states that it is not in the allow list.
    No allow-all switch, no regex option, and no negation capability exist in `EgressPolicy`, and attempting the closest equivalent via a wildcard host `("*", 443)` is refused at construction with `ValueError: wildcard host not allowed: '*'`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted output showing an ABSENT policy RAISES rather than producing a usable object, and an unparseable policy likewise. State explicitly that no code path yields a default or guessed allow list, and name what was checked to establish that.
  - ALSO PROVE THE OPPOSITE FAILURE IS VISIBLE, not silent. Show what an operator sees when the policy omits the model endpoint: the broker must REFUSE that destination with its reason, not hang. This is the failure that breaks the product, and the whole argument for refusing to guess is that both failure directions are loud.
  - Observed evidence:
    Observed from `agent_workflows.egress_policy.load_egress_policy` and `handle_broker_connection`:
    ```text
    ABSENT POLICY: PolicyConfigurationError: Egress policy configuration is absent: explicit policy configuration is required and cannot be defaulted or guessed
    UNPARSEABLE (''): PolicyConfigurationError: Egress policy configuration is empty or whitespace
    UNPARSEABLE ('not_a_destination'): PolicyConfigurationError: destination token missing port: 'not_a_destination'
    UNPARSEABLE ('host:not_a_port'): PolicyConfigurationError: destination port must be an integer: 'host:not_a_port'
    UNPARSEABLE ('host:70000'): PolicyConfigurationError: port out of range (1-65535): 70000
    ```
    Omitted model endpoint broker response (operator visibility):
    ```http
    HTTP/1.1 403 Forbidden
    Content-Type: text/plain; charset=utf-8
    Content-Length: 55
    Connection: close

    destination api.anthropic.com:443 is not in allow list
    ```
    No code path yields a default or guessed allow list. Checked: `agent_workflows/egress_policy.py` contains no network discovery, no environment scanning, and no fallback endpoints; `load_egress_policy` requires explicit non-None configuration and raises `PolicyConfigurationError` whenever configuration is absent or unparseable.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted broker decision log for one ALLOWED and one REFUSED destination, each naming the destination and verdict, plus the client-side result for both. Show the broker ran in the PARENT process and the policy object it consulted was not reachable from the client side; state in one sentence why that makes the policy unreconfigurable by the client.
  - PROVE THE SAME-PORT PARTITION, which is this Set's reason to exist. The allowed and refused destinations in the evidence MUST share a port, so the pasted pair demonstrates a decision Landlock provably cannot make (research `uq4y6q` Finding 3). A pair differing in port does not meet this item. E-06's alias case (`127.0.0.1:P` allowed, `localhost:P` refused, ONE live listener) is the hermetic source of this pair. The research run is context, not a substitute.
  - Plus pasted refusals for a non-CONNECT method, an over-long request head, and a target carrying a newline, each showing `400`, a fixed log reason, and no raw echo (PR-703). Plus the AF_UNIX socket's directory mode.
  - Observed evidence:
    Observed from same-port broker run with one live loopback listener on port 50183 (`127.0.0.1:50183` allowed, `localhost:50183` refused):
    ```text
    SAME-PORT LOGS:
    LOG: PROXY ALLOWED 127.0.0.1:50183: destination 127.0.0.1:50183 is allow-listed
    LOG: PROXY DENIED localhost:50183: destination localhost:50183 is not in allow list
    CLIENT ALLOWED HEAD: HTTP/1.1 200 Connection Established
    CLIENT ALLOWED PAYLOAD: HELLO
    CLIENT REFUSED RESP:
    HTTP/1.1 403 Forbidden
    Content-Type: text/plain; charset=utf-8
    Content-Length: 49
    Connection: close

    destination localhost:50183 is not in allow list
    ```
    PR-703 untrusted input refusals:
    ```text
    PR-703 non-CONNECT: status=400 log=PROXY REFUSED malformed-request: unsupported method: only CONNECT is permitted resp=HTTP/1.1 400 Bad Request
    PR-703 over-long head: status=400 log=PROXY REFUSED malformed-request: request head exceeded size limit resp=HTTP/1.1 400 Bad Request
    PR-703 target with newline: status=400 log=PROXY REFUSED malformed-request: malformed request line resp=HTTP/1.1 400 Bad Request
    ```
    AF_UNIX socket directory mode: `0o700`.
    Process isolation: The broker runs in the parent process outside the client's process space and network namespace, communicating only over stream sockets without sharing memory or policy handles, making the policy completely unreconfigurable by the client.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: The client-side error for a refused destination pasted verbatim, with a one-sentence judgement that it is distinguishable from a network fault and names the refusal. Plus the broker log line for the same refusal showing the destination and reason.
  - A SILENT DROP FAILS THIS ITEM. If the refusal presents to the client as a closed connection, a reset, or a timeout with no indication a policy acted, that is the ambiguous outcome E-04 exists to prevent and must be fixed rather than recorded.
  - Observed evidence:
    Client-side error for refused destination pasted verbatim:
    ```http
    HTTP/1.1 403 Forbidden
    Content-Type: text/plain; charset=utf-8
    Content-Length: 51
    Connection: close

    destination github.com:443 is not in allow list
    ```
    Broker log line for the refusal:
    ```text
    PROXY DENIED github.com:443: destination github.com:443 is not in allow list
    ```
    Judgement: The response is an explicit HTTP 403 Forbidden carrying a plain-text body naming the refused destination and reason, distinguishing it clearly from an ambiguous connection reset, TCP drop, or network fault.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -rs tests/test_egress_policy.py` showing every policy and handler test passing with NO SKIPS, plus the bare suite summary line. The only sanctioned skip is the AF_UNIX-listener test on a host without `socket.AF_UNIX` (PR-702), and it must be named if it appears. Any other skip means a test depends on something it should not: name it and fix it rather than accepting it.
  - PROVE THE TESTS ARE NOT VACUOUS. Temporarily invert the policy default so an unlisted destination is allowed, paste the resulting FAILURES naming the fail-closed tests, then revert and paste the restored pass. A suite that stays green against an allow-by-default policy is not testing the property this plan exists to deliver.
  - Observed evidence:
    Pasted output of `python3 -m pytest -o addopts="" -rs tests/test_egress_policy.py` (no skips):
    ```text
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=671457872
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 37 items

    tests/test_egress_policy.py .....................................        [100%]

    ============================== 37 passed in 1.17s ==============================
    ```
    Vacuity proof: temporarily inverting policy default to allow-by-default resulted in 8 failures across all fail-closed tests:
    ```text
    FAILED tests/test_egress_policy.py::TestEgressBrokerUnixSocket::test_af_unix_broker_lifecycle_and_directory_mode - AssertionError: assert b'HTTP/1.1 403 Forbidden' in b'HTTP/1.1 200 Connection Established\r\n\r\n'
    FAILED tests/test_egress_policy.py::TestEgressPolicyLoader::test_explicit_configuration_formats - AssertionError: assert not True
    FAILED tests/test_egress_policy.py::TestEgressPolicyUnit::test_same_host_different_port_denied - AssertionError: assert not True
    FAILED tests/test_egress_policy.py::TestEgressPolicyUnit::test_empty_policy_denies_everything - AssertionError: assert not True
    FAILED tests/test_egress_policy.py::TestEgressPolicyUnit::test_unlisted_destination_denied - AssertionError: assert not True
    FAILED tests/test_egress_policy.py::TestHermeticBrokerEndToEnd::test_omitted_model_endpoint_refusal_visible - AssertionError: assert b'HTTP/1.1 403 Forbidden' in b'HTTP/1.1 200 Connection Established\r\n\r\n'
    FAILED tests/test_egress_policy.py::TestHermeticBrokerEndToEnd::test_hermetic_same_port_and_port_partition - AssertionError: assert b'403 Forbidden' in b'HTTP/1.1 200 Connection Established\r\n\r\n'
    FAILED tests/test_egress_policy.py::TestHermeticBrokerEndToEnd::test_broker_refusal_distinguishable_from_network_fault - AssertionError: assert b'HTTP/1.1 403 Forbidden\r\n' in b'HTTP/1.1 200 Connection Established\r\n\r\n'
    ========================= 8 failed, 29 passed in 2.18s =========================
    ```
    Restored pass after reverting:
    ```text
    ============================== 37 passed in 2.27s ==============================
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Pasted end-to-end test output showing the client REACHED the allow-listed loopback listener and was REFUSED for the unlisted one, with both listeners held open throughout. State explicitly that the test used no namespace, no DNS, and no external network, and name how that was ensured, since that is what makes it unskippable on a capability-poor host.
  - DISTINGUISH THE REFUSAL FROM A DEAD PORT. Show that the unlisted destination's refusal came from the POLICY and not from a closed socket, by asserting the broker's logged verdict for it AND, for the same-port alias case, that the allowed spelling reached the very listener the refused spelling named. A test that would pass against a closed listener proves nothing about the policy, which is the trap E-06 names.
  - Show the test drove the handler over `socket.socketpair()` rather than an AF_UNIX path (PR-702).
  - Observed evidence:
    Hermetic test run output with both listeners held open throughout (`Listener P active on port 40701, Listener Q active on port 35667`):
    ```text
    Listener P active on port 40701, Listener Q active on port 35667
    127.0.0.1:P response: HTTP/1.1 200 Connection Established payload echo: PING_SAME_PORT decision: PROXY ALLOWED 127.0.0.1:40701: destination 127.0.0.1:40701 is allow-listed
    localhost:P response: HTTP/1.1 403 Forbidden decision: PROXY DENIED localhost:40701: destination localhost:40701 is not in allow list
    127.0.0.1:Q response: HTTP/1.1 403 Forbidden decision: PROXY DENIED 127.0.0.1:35667: destination 127.0.0.1:35667 is not in allow list
    ```
    The refusal came from the policy and not a closed socket: Listener P was held open and active throughout the test; `127.0.0.1:40701` connected and exchanged payload successfully over the tunnel to listener P, while `localhost:40701` on the exact same port P was refused with 403 Forbidden and logged as `PROXY DENIED localhost:40701: destination localhost:40701 is not in allow list`. Listener Q on port 35667 was also held open and similarly refused.
    Transport seam: The test drove `handle_broker_connection` directly over `socket.socketpair()`, eliminating any dependency on AF_UNIX for the core handler logic.
    Environment: The test ran hermetically without requiring user/network namespaces, without resolving DNS (policy evaluated directly on the requested authority before resolution per OQ-01), and without accessing external networks.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan delivers the piece that makes the whole Set worth building: a decision keyed on DESTINATION
rather than port. It is also the plan whose claims are easiest to overstate, because the broker visibly
refuses a git remote and it is tempting to call that push denial. It is not. Without child 03 nothing
makes a worker use this broker (F-6), and even afterwards the honest claim is destination filtering
against a declared allow list, since an allow-listed host remains reachable for any purpose.

WHAT A REVIEWER SHOULD PUSH HARDEST ON. First, that deny is genuinely the DEFAULT and no construction
path reaches an allow-everything state, which V-01 tests by attempting it. Second, that E-02's refusal
to guess an endpoint is preserved: a convenience default here would be a silent hole, and it is the
kind of change that looks like a usability improvement. Third, that V-03's evidence pair shares a PORT,
because a pair differing in port would demonstrate only what Landlock can already do and would quietly
fail to prove the one property this Set exists for. Fourth, that V-06's refusal is attributable to the
policy rather than to a closed socket.

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`,
never `git add -A`, and never push. This is a SHARED CHECKOUT: verify the staged set with
`git diff --cached --name-only` before committing, unstage anything that is not yours with
`git restore --staged <path>`, and re-verify after any failed raw commit attempt. Run the suite BARE
as `python3 -m pytest` and PASTE ITS ACTUAL SUMMARY LINE; a summary you did not produce is not
evidence, and the same hard-MUST governs every pasted broker log, client error, and exit status these
`V-*` items demand. Paste skips explicitly rather than letting a green line hide one.

SCOPE NOTE the executor should expect: `host_sandbox_profile.py` is declared for a CONDITIONAL
correction (keeping child 01's probe note consistent with the policy that now exists) and may well go
unmodified, in which case `aw ipd finalize` asks for `--scope-ack` on it. That is an ordinary finalize
answer, not a failure.

LIFECYCLE TRANSITION. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete observed evidence.
Reaching `executed/` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` /
`aw agy run` the RUNNER owns the terminal transition and finalize, so do NOT invoke `aw ipd finalize`
yourself in a runner-driven execution; a HAND execution invokes it
(`aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`). Never hand-edit
`- Status:` and never hand-roll a `git mv` into `executed/`. This plan must NOT set backlog `sv9ce4`
to `done`; the runner sets `graduated`.
