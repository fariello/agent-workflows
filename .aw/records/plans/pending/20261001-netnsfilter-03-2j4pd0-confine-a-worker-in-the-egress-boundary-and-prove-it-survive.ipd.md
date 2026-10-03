# IPD: Confine a worker in the egress boundary and prove it survives teardown attempts

- Date: 2026-10-01
- Kind: child
- Concern: Children 01 and 02 deliver a probed partition and an enforcing broker, but nothing makes a real worker use either, so no boundary exists yet. This is also where the design can silently become a convention instead of a boundary: a worker placed in a namespace it created is root in that namespace and can delete the rules confining it. Measured during authoring (research `akmzyq` Finding 6), the naive arrangement was torn down in ONE command, `FLUSH SUCCEEDED`.
- Scope: Wire the egress boundary into the hardened execution profile so a confined worker reaches allow-listed destinations through the broker and nothing else, create the namespace in the PARENT, drop `CAP_NET_ADMIN` before handing off, and prove non-evadability by attempting teardown from inside and verifying refusal from OUTSIDE. Hardened remains opt-in and fails closed where the capability is absent.
- Scope-Paths: agent_workflows/host_sandbox_profile.py, agent_workflows/oc_runipd.py, agent_workflows/egress_policy.py, tests/test_host_sandbox_profile.py, tests/test_egress_confinement.py
- Item-Dependencies: executed:rozdkp
- Status: to-review
- From-Backlog: sv9ce4
- From-Spec: 25kzda
- Work-Kind: feature
- Priority: low
- Set: netnsfilter
- Order: 3
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 2j4pd0

## Workflow history

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
  - ORDER IS LOAD-BEARING. Everything privileged must happen before the worker's first instruction, for the same reason `landlock_bootstrap_source` applies its ruleset before `execvp`: a boundary installed after the worker starts is a boundary the worker could have acted ahead of. Measured context: loopback inside the namespace works after `ip link set lo up` and needs no `slirp4netns` (research `akmzyq` Finding 2).
  - Depends on: E-01
  - Expected outcome: A worker that starts already confined, with the broker reachable and no other route out, and with every privileged setup step completed by the parent.
  - Execution state: pending

- [ ] E-03 DROP `CAP_NET_ADMIN` (and any other capability that permits altering network configuration) before handing off to the worker, so the confined process cannot modify what confines it. This is the item that makes the difference between a boundary and a convention, and it must be verified rather than assumed.
  - THE NAIVE ARRANGEMENT IS EVADABLE IN ONE COMMAND, MEASURED. Research `akmzyq` Finding 6: a process placed in a namespace it created is root there, and flushing the filtering rules printed `FLUSH SUCCEEDED -> boundary is EVADABLE` with the rule gone afterwards. The CORRECTED arrangement, parent installs then drops the capability, was measured refusing the same attempt: `[agent] flush rc=4 out=iptables ... Permission denied (you must be root)`, with the parent's own post-attempt check showing the rule still present. BUILD THE SECOND ARRANGEMENT, never the first.
  - Depends on: E-02
  - Expected outcome: A confined worker whose attempt to alter the network configuration fails, with the confinement intact afterwards as seen from the parent.
  - Execution state: pending

- [ ] E-04 Wire the boundary into `oc_runipd._apply_execution_profile` so the `hardened` profile applies it, preserving the existing fail-closed posture exactly: `select_execution_profile` already raises `HardModeUnavailableError` rather than degrading when hardened is unavailable, and hardened already refuses without an isolated lane. Requesting hardened on a host whose EXECUTED egress probe reports False must REFUSE, never silently run unfiltered. Leave the default profile byte-unchanged, so nothing changes for a run that did not ask for hardening.
  - DO NOT WEAKEN CHILD 01'S FAIL-CLOSED PATH to make hardened reachable on an incapable host. The correct outcome there is that hardened egress filtering is unavailable and says so, which is the established pattern in this module rather than a new one.
  - Depends on: E-03
  - Expected outcome: `hardened` gains egress filtering where the probe proved the capability, and refuses loudly where it did not. The default profile is unaffected.
  - Execution state: pending

### Task group 2: proof

- [ ] E-05 Add `tests/test_egress_confinement.py` proving the boundary end to end with a REAL subprocess, using parent-held endpoints so the test needs no external network: a confined worker reaches an allow-listed destination and is REFUSED for an unlisted one on the SAME port. Also assert the default profile's argv is unchanged, so the additive guarantee is pinned rather than claimed. Skip only where the host cannot create a namespace, and make that skip state WHICH guarantee is consequently unverified.
  - Depends on: E-04
  - Expected outcome: The same-port destination partition is pinned by a test driving a real confined process, which is the property no existing test in this repository covers.
  - Execution state: pending

- [ ] E-06 Add the ADVERSARIAL test: a confined worker attempts to escape and each attempt is verified to fail, modeled on the existing `AdversarialOsDenialTests` in `tests/test_host_sandbox_profile.py`, which already proves filesystem denials this way. Cover the attempts measured during authoring: tearing down the filtering rules; connecting directly to a denied destination by raw address; reaching a denied destination on a different port; and nesting a fresh namespace to escape. VERIFY EVERY OUTCOME FROM OUTSIDE the sandbox, never by asking the confined process whether it is still confined.
  - FIVE EVASIONS WERE MEASURED HOLDING (research `akmzyq` Finding 4): proxy variables removed gave `Could not resolve host: github.com`; a raw-address CONNECT was refused `403`; port 22 was refused `403`; a nested `unshare` still reported `Network is unreachable`; and the allow-listed destination still succeeded with `rc: 0`. That last row is part of the test, not a footnote: a boundary that also breaks the model API is not a product.
  - A METHODOLOGY TRAP WORTH NAMING, because it nearly produced a false pass during authoring: the first version of the teardown measurement piped `iptables` through `head`, so the pipeline's exit status masked the real one and it printed `FLUSH SUCCEEDED` for a flush that had actually been REFUSED. Do not judge a teardown attempt by a piped command's exit status; read the rules from the parent afterwards.
  - Depends on: E-05
  - Expected outcome: Each evasion attempt is pinned as refused, with the refusal established by the parent's own view, and the allow-listed path still working.
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
| F-9 | The hardened profile is OPT-IN and has no CLI flag | `_apply_execution_profile` returns `argv` unchanged unless `execution_profile` is `hardened` in the operator's own `runner-profiles.json`; the deliberate absence of a flag is recorded because "a documented flag on a cross-platform tool reads as a cross-platform guarantee" | Nothing changes for a default run, which bounds this plan's blast radius. It also means the boundary protects only runs that asked for it, which child 04 must state honestly. |

## Proposed changes (ordered, validatable)

1. Carry an optional egress boundary through the sandbox plan and launcher, defaulted off so the
   default path is byte-unchanged (E-01).
2. Create the namespace, install the policy, and start the broker in the PARENT before the worker
   exists (E-02).
3. Drop `CAP_NET_ADMIN` before handing off, which is what makes the confinement non-evadable (E-03).
4. Wire it into the hardened profile, preserving the existing fail-closed refusals (E-04).
5. Pin the same-port destination partition with a real confined subprocess (E-05).
6. Pin every measured evasion as refused, verified from outside the sandbox (E-06).

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
  and what this plan removes is the worker's ROUTE to a denied remote, not its credentials.
  - Carrier: sv9ce4

## Scope check

- Over-scope: none. `host_sandbox_profile.py` is changed by E-01 through E-03; `oc_runipd.py` by E-04;
  `egress_policy.py` by whatever the broker needs to be startable by the parent at launch, which is
  this plan's consumer-side half of child 02's module; `tests/test_host_sandbox_profile.py` by the
  default-path-unchanged assertion in E-05; `tests/test_egress_confinement.py` is NEW.
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
- The DEFAULT profile's argv must be proven unchanged, pasted, since that is what keeps this plan
  additive.
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
- `host_sandbox_profile`'s module docstring states "Network scoping and container isolation are out of
  scope here", which this plan makes false. Child 04 amends it in the same pass as the spec so the two
  cannot drift. That is a known, deliberate, one-child window and not an oversight.
- `docs/runner-profiles.md` documents the hardened profile for operators and will need the egress
  boundary described, including that it is Linux-only, opt-in, and OpenCode-only. Child 04 owns it,
  for the same reason: operator documentation written before the limits are measured is the overclaim
  this Set exists to avoid.
- No CHANGELOG entry here: child 04 records the Set's user-visible change once.

## Open questions

### OQ-01: Should the worker receive the broker address through the environment or through argv?

- Blocking: no
- Status: resolved
- Owner: none
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
- Owner: none
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
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM THE NAMESPACE'S OWN BEHAVIOR: the worker loses all
  egress, which is the fail-closed direction and requires no additional mechanism. Because the
  namespace has no route (F-6), a dead broker means destinations become unreachable rather than
  unfiltered, so the dangerous failure (traffic escaping unchecked) is not reachable by killing the
  broker. What this plan DOES owe is distinguishability, which E-04 of child 02 already requires for
  refusals: a broker that has died must not look like a policy refusal, so the worker's failure should
  be reported as an infrastructure fault. That is a reporting concern rather than a safety one, and it
  is why this question is non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted proof that `enter_sandbox` called WITHOUT an egress boundary produces byte-identical output to today's, for example a captured digest compared before and after, plus the pasted result of the existing `EnterSandboxTests` and `LandlockBootstrapTests` still passing. Then the launcher produced WITH a boundary, showing both the Landlock rules and the namespace wrapper present in one launch path.
  - PROVE THE FILESYSTEM PARTITION SURVIVED. Paste the existing `AdversarialOsDenialTests` passing, since those are what prove a hardened worker cannot write the control, main or sibling trees. Adding a network axis must not cost the axis this repository already had, and a green overall suite alone does not demonstrate that specifically.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted evidence that every privileged setup step completed in the PARENT before the worker started: the namespace created, loopback up, the policy installed, the broker listening. Show the ordering, for example by the parent's own log timestamps or a sequenced test assertion, plus the broker address as the worker received it.
  - PROVE THE NAMESPACE HAS NO OTHER ROUTE OUT, which is what F-6 rests on and what makes the boundary independent of worker cooperation. Paste a direct outbound attempt from inside the namespace with NO proxy configuration showing it fails, and state the error verbatim.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output of the confined worker attempting to tear down its own boundary, showing the attempt REFUSED with its exact error, followed by the PARENT's own check showing the filtering configuration still intact. Both halves are required: the refusal alone does not prove the rules survived.
  - THE AUTHORITATIVE CHECK IS THE PARENT'S, AND A PIPED EXIT STATUS IS NOT EVIDENCE. Do not judge the teardown by a piped command's status: during authoring exactly that masked the real status and printed `FLUSH SUCCEEDED` for a flush that had been REFUSED (F-3). Paste the parent's unpiped view of the rules after the attempt, and state explicitly that the verdict came from outside the sandbox.
  - ALSO CONFIRM THE CAPABILITY IS ACTUALLY GONE rather than merely unused: paste the worker's own capability set, or an attempt at a second distinct network-configuration change, so the drop is demonstrated and not inferred from one refused command.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted proof of three dispatch outcomes: the DEFAULT profile returning argv unchanged; `hardened` on a capable host producing a confined launcher; and `hardened` on a host whose egress probe reports False REFUSING with the existing fail-closed error rather than running unfiltered. Force the third through the `forced_runner_safety_verdicts` seam rather than requiring an incapable host, so it is verified on every machine including this one.
  - NOTHING MAY SPAWN IN THE REFUSAL CASE. Follow the pattern of the existing `test_hard_mode_requested_without_capability_fails_closed`, which patches `Popen` to prove no process starts. A refusal that still launched the worker unfiltered would be the exact fail-open outcome this item exists to prevent, and a raised exception alone does not rule it out.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted test output showing a REAL confined subprocess reaching an allow-listed destination and being REFUSED for an unlisted one ON THE SAME PORT, with the client-side result for each. A pair differing in port does not meet this item, because that is a decision the Landlock mechanism could already make and would not demonstrate this Set's reason to exist.
  - If the test SKIPPED because the host cannot create a namespace, paste the skip reason and state plainly which guarantee is consequently unverified here. Do not let a green summary line stand in for a skipped boundary test.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted result for EACH of the four evasion attempts (teardown, raw-address connect, denied destination on another port, nested namespace), each showing the attempt failed and each verified from OUTSIDE the sandbox. Plus the fifth row: the allow-listed destination still succeeding, which proves the boundary did not take the product with it.
  - PROVE THE ADVERSARIAL TESTS ARE NOT VACUOUS. Temporarily remove the capability drop so the naive arrangement is restored, paste the resulting FAILURE of the teardown test, then revert and paste the restored pass. F-1 measured that arrangement succeeding in one command, so a test suite that stays green against it is not testing non-evadability at all, and that is the single defect most likely to ship unnoticed from this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This is the plan where the Set either delivers a boundary or ships a convention, and the difference is
one capability drop. A reviewer should treat E-03 and V-06 as the center of the plan: research
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
