# IPD: Comms broker discovery registry of live OpenCode targets (filesystem descriptor, mDNS optional)

- Date: 2026-09-24
- Kind: child
- Concern: Child 01 (`nomhl1`) makes the broker take an explicit `--target-url`, because an OpenCode instance's server port is ephemeral by default (`opencode serve --help`: "--port ... [default: 0]") and nothing records which instance serves which agent. Backlog `lbhmi3` ("agent-comms IPD 4: broker discovery/registry of live targets (mDNS/attach + filesystem fallback)") closes that gap. The spec's Deferred list names it: "Discovery/registry (mDNS / attach / filesystem descriptor), cross-instance reachability."
- Scope: IN: a same-box FILESYSTEM registry. An opted-in instance's operator (or a wrapper) writes a small JSON descriptor into `untracked/registry/` via `python3 -m agent_workflows.comms_broker register --agent <proj.agent> --url <loopback url> --mode tui|headless [--session <id>]`; the broker gains `--target-agent` resolution from that registry, verifying liveness with `GET /global/health` and that `GET /path` `directory` matches the repo root before nudging. Stale descriptors are skipped and reported, never deleted by the broker. OUT: mDNS browsing (no stdlib mDNS client; see Deferred), cross-box reachability, auto-registration from inside OpenCode (would need a plugin), any change to the envelope or ack enum.
- Scope-Paths: agent_workflows/comms_broker.py, tests/test_comms_broker_registry.py, .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md
- Item-Dependencies: executed:nomhl1
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- From-Backlog: lbhmi3
- Set: commsbroker
- Order: 2
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: ex539u
- Approval: 2026-09-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-25 approved (aw set): status set to approved

- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. 6 findings PR-901..PR-906, all FIXED; 5 decisions D-1..D-5 recorded; `aw ipd lint` conforming at `--phase author` before review and at `--phase review-finalize` after. F-1's two route schemas, F-2's `import zeroconf` failure and the stdlib-only dependency claim were all re-verified and HOLD, as were `comms.BROKER_ACK_STATES` containing both failure states and `comms.ack_writer_for` returning `broker` for each. THE FINDING THAT RESHAPED THE PLAN is PR-901: a descriptor is UNTRUSTED INPUT and E-03 opened two NEW outbound sockets to it with no policy. `untracked/registry/` is gitignored and locally writable, so a descriptor's `url` flows from an unvetted file into `/global/health` and `/path`, while child 01 guards its one outbound call with `url_policy_refusal` PLUS a redirect-refusing opener whose own review recorded that a bare entry check misses a `302 Location: http://evil/` from a loopback server; E-03 named neither symbol (E-01 said only 'the same check child 01 added') and trusted registration-time validation for a file that may since have been replaced. Both calls now route through the shipped policy and opener, E-03 re-validates on read, and E-08 adds four trust-boundary cases whose evidence is the fixture's ZERO-request count, because an unguarded resolver that connects and then fails returns the same ack state as a guarded one that never connects. SECOND, PR-902: `/path` returns BOTH `directory` and `worktree` (F-1 records both) and the plan compared one with no stated reason - measured, THREE live worktrees of this repo run simultaneously sharing one `worktree` value while each has its own `directory` and its own comms lane, so comparing the wrong key would let a broker in one lane nudge another lane's instance; E-04 now fixes `directory` as authoritative, puts the reason in the docstring, and is verified by a sibling fixture sharing the `worktree` value. THIRD, PR-903: E-04's failure ack had no message and no idempotence rule - `comms.ack_filename` REQUIRES a msg-id while a resolution failure is a property of the target, and at child 01's 10-second default a target down for an hour would rewrite one ack about 360 times against a sibling plan's already-pinned non-rewrite invariant; E-06 defines one ack per eligible message with no rewrite, verified by two `st_mtime_ns` values. Also fixed: the conventions bullet described the comms dir by an existence fallback that child 01's review explicitly corrected to `engine.resolve_target_layout` plus `_record_scaffold_dirs`; the descriptor-writer trust question is now an explicit Deferred row with its bounded consequence stated (a misdirected CONTENT-FREE nudge, never a payload disclosure, because the broker is payload-blind); and the gate gained its approval statement, per-symbol scope fence, honesty rule naming the three fakeable claims, stop conditions and conditional finalize ownership. Recorded as verified-and-unchanged: the filesystem-over-mDNS choice, the never-delete-a-stale-descriptor rule, the gitignore claim (probed in both layouts), the per-repo-root registry that bounds the flat `<agent>.json` naming, and the directory-mismatch mutation proof, which was already well designed. A pre-existing suite failure (`test_blast_radius_zero_across_pending_plans`, stranded prereq `72qlya`) is recorded so V-10 cannot absorb it.
- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog lbhmi3; re-measured the OpenCode 1.18.32 `/doc` for the liveness and identity routes (`/global/health` returns `healthy`+`version`, `/path` returns `directory`) and confirmed no mDNS client is importable (`import zeroconf` fails; runtime deps are `filelock` only).

## Goal

Let the broker find a live, correct target by agent name on the same box instead of requiring a hand-typed URL, without adding a dependency and without trusting a descriptor it has not verified.

A DESCRIPTOR IS UNTRUSTED INPUT, AND THE PLAN'S FIRST DRAFT DID NOT SAY SO (F-4, the review's dominant finding). `untracked/registry/` is a gitignored local directory, so any local process may drop an `<agent>.json` naming any loopback URL and port, INCLUDING an agent that just processed a hostile inbox message. That makes the descriptor's `url` a value flowing from an untrusted file into two NEW outbound HTTP calls (`/global/health`, `/path`) that child 01's threat model never covered: `nomhl1` guards its ONE outbound call with `url_policy_refusal` plus a `RefusingRedirectHandler` that re-checks EVERY redirect target, and its own review recorded that a bare entry-point check misses the redirect case. E-03 as authored named neither, so the registry path would have opened two unguarded sockets to a disk-supplied URL. The remedy is not a new mechanism: `resolve_target` MUST route both calls through `url_policy_refusal` and the redirect-refusing opener child 01 ships, and the spec's existing "Untrusted-input stance" is the contract this inherits rather than a new one this plan invents.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: registry

- [ ] E-01 Add `comms_broker.REGISTRY_SUBDIR = "registry"` under the comms `untracked/` lane and a descriptor schema `{"agent", "url", "mode", "session", "pid", "registered_at"}` with `validate_descriptor(obj)` returning a problem list. `agent` must pass `comms.is_filename_safe`, `url` must be refused by nothing in `comms_broker.url_policy_refusal` (child 01 E-09's SYMBOL, named explicitly rather than as "the same check child 01 added": it refuses a non-http(s) scheme and any host outside `{"localhost", "127.0.0.1", "::1", "[::1]"}`), `mode` in `tui|headless`, `session` required when `mode == "headless"`. Verified at review: the lane is gitignored in BOTH layouts, by `repo/.aw/.gitignore`'s `records/*/untracked/` in the canonical layout (probed: `git check-ignore -v` on a `untracked/registry/probe.json` matches that line) and by the nested `.agents/comms/.gitignore` in legacy, per the spec's Gitignore paragraph.
  - Depends on: none
  - Expected outcome: a pure validator; no I/O; it REUSES `url_policy_refusal` rather than re-encoding the loopback set, since two encodings of one policy is how they drift.
  - Execution state: pending
- [ ] E-02 Add the `register` and `unregister` subcommands: write `untracked/registry/<agent>.json` atomically (temp file then `os.replace`) after validation, and remove it on `unregister`. Registration is always an explicit human or wrapper act; nothing registers implicitly.
  - Depends on: E-01
  - Expected outcome: `register` creates one valid descriptor file; `unregister` removes it; an invalid descriptor exits 2 and writes nothing.
  - Execution state: pending
- [ ] E-03 Add `comms_broker.resolve_target(comms_dir, agent, repo_root, *, opener)`: load the descriptor, RE-VALIDATE it with `validate_descriptor` (a descriptor is read from a gitignored directory any local process may write, so trusting the value written at `register` time would trust a file that may have been replaced since), then `GET <url>/global/health` (must return `"healthy": true`) and `GET <url>/path`. Return the descriptor on success, or an ack state on failure: missing descriptor, a descriptor failing re-validation, or a refused connection -> `agent-not-running`; unhealthy, timeout or directory mismatch -> `agent-not-responding`. Never deletes a stale descriptor. BOTH CALLS GO THROUGH CHILD 01'S URL POLICY, which E-03 originally omitted and which is the whole trust boundary (F-4): call `url_policy_refusal(url)` BEFORE opening any socket, and make the two GETs use child 01's redirect-refusing opener (`RefusingRedirectHandler`, whose review recorded that a bare entry-point check misses a `302 Location: http://evil/` from a loopback server), not a bare `urllib` opener.
  - Depends on: E-02
  - Expected outcome: a resolver that refuses an instance serving a different directory, AND refuses a disk-supplied non-loopback URL and a redirect to one, without ever opening a socket to either.
  - Execution state: pending
- [ ] E-04 Decide the `/path` comparison against BOTH keys, not `directory` alone, because this repository routinely runs agents in git worktrees and `directory` alone is ambiguous there (F-5). `/path`'s 200 schema has required `directory` AND `worktree` (F-1 records both and the plan then used one). Measured at review: three live worktrees of this repo exist simultaneously, all sharing one `--git-common-dir`, and each carries its own `.aw/records/comms` lane. So state the rule explicitly in `resolve_target`'s docstring and implement it: compare `os.path.realpath(directory)` to `os.path.realpath(repo_root)` as the AUTHORITATIVE check (it is the per-worktree path, which is what "is this instance serving MY tree" means), and treat `worktree` as recorded-but-not-compared, with a one-line reason for why a `worktree` match is NOT sufficient (two lanes of one repo share it, so matching on it would let a broker in one lane nudge the instance of another).
  - Depends on: E-03
  - Expected outcome: the docstring names both keys and which one decides; a fixture serving a SIBLING worktree's `directory` with the SAME `worktree` is refused.
  - Execution state: pending
- [ ] E-05 Wire `run`: `--target-url` stays accepted; when it is omitted, the broker calls `resolve_target` for `--target-agent` on every scan (so a restarted instance with a new port is picked up after it re-registers) and writes the resulting failure state as the broker ack instead of attempting delivery.
  - Depends on: E-04
  - Expected outcome: explicit URL behaves exactly as in child 01; registry path used only when no URL is given.
  - Execution state: pending
- [ ] E-06 Define WHICH MESSAGE a resolution-failure ack attaches to, and make it idempotent, because E-05 as authored specifies neither and an ack is keyed on a message (F-6). `comms.ack_filename(msg_id, from_agent, state)` requires a `msg_id`, but a resolution failure is a property of the TARGET, not of one message. Rule: write the failure ack ONCE PER ELIGIBLE MESSAGE that the scan would otherwise have nudged (so the ack lands on a real msg-id and a message nobody sent gets no ack), and do NOT rewrite an existing ack in the same state for that msg-id. The idempotence half is not optional: child 01 already pins the equivalent invariant for its `scheduled` ack ("a second `scan_once` on the same not-yet-due message does NOT rewrite the `scheduled` ack (compare `st_mtime_ns`)"), and with child 01's `--interval` default of 10 seconds an instance down for one hour would otherwise rewrite the same ack about 360 times. Reuse child 01's existing already-acked skip rather than adding a second mechanism.
  - Depends on: E-05
  - Expected outcome: a down target produces one `agent-not-running` ack per eligible message and no rewrites across repeated scans.
  - Execution state: pending

### Task group 2: tests, spec, suite

- [ ] E-07 Write `tests/test_comms_broker_registry.py` with a loopback `http.server` fixture serving `/global/health` and `/path`: valid registration round-trip; invalid descriptor rejected (non-loopback URL, headless without session, unsafe agent name); directory mismatch -> `agent-not-responding` and no nudge request; missing descriptor -> `agent-not-running`; stale descriptor left in place; explicit `--target-url` bypasses the registry. NO TEST MAY START A REAL `opencode` OR TOUCH A HUMAN'S RUNNING INSTANCE: the fixture is a local `http.server`, matching child 01's stated rule, so the suite stays hermetic on a machine with no OpenCode installed.
  - Depends on: E-06
  - Expected outcome: all pass; the directory-mismatch test fails under the mutation named in V.
  - Execution state: pending
- [ ] E-08 Add the FOUR trust-boundary and idempotence cases an ordinary happy-path suite misses, each pinning one of the review findings rather than re-testing the happy path. (a) A descriptor whose `url` is NON-LOOPBACK is refused by `resolve_target` with NO socket opened (assert the fixture recorded zero requests, not merely that the result was a failure state). (b) A descriptor pointing at a loopback fixture that answers `302 Location: http://evil.example/` is refused, which is the case child 01's review recorded a bare entry check missing. (c) A descriptor REPLACED ON DISK between `register` and `resolve_target` with a non-loopback URL is refused, proving E-03 re-validates rather than trusting registration-time validation. (d) Two consecutive scans against a DOWN target leave the failure ack's `st_mtime_ns` UNCHANGED (paste both values), the idempotence invariant E-06 adds and child 01 already pins for its `scheduled` ack.
  - Depends on: E-07
  - Expected outcome: all four pass, and (a) and (b) demonstrate refusal BEFORE any request reaches the fixture.
  - Execution state: pending
- [ ] E-09 Amend the spec: add a "Broker target registry (optional)" subsection (descriptor path and schema, the two verification calls AND that both go through the loopback plus redirect policy, the `directory`-not-`worktree` comparison rule, stale handling, mDNS deferred) and move filesystem discovery out of the Deferred bullet, leaving mDNS and cross-instance reachability deferred. Write the SECTION BODY ONLY: do NOT hand-edit the spec's `- Status:` (it stays `implemented`) or its `## Workflow history`, which `.aw/records/specs/README.md` forbids and routes through `aw specs note <path> --message <text>`; use that verb for the note line rather than editing the block by hand. An `implemented` spec is amendable in place (AGENTS.md: "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT") and this plan declares it in `- Scope-Paths:`.
  - Depends on: E-08
  - Expected outcome: the spec matches shipped behavior.
  - Execution state: pending
- [ ] E-10 Run the bare suite `python3 -m pytest`.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07, E-08, E-09
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Runtime dependencies are `dependencies = ["filelock>=3"]` (`pyproject.toml`); stdlib only.
- The comms directory is chosen per layout in `engine`; child 01's entry point already follows it. STATE IT AS CHILD 01'S REVIEW CORRECTED IT, not as a path fallback: `engine` selects on LAYOUT via `engine.resolve_target_layout` (`.aw/system` present -> `aw`, else `.agents/workflows` present -> `legacy`, else `aw`) and `engine._record_scaffold_dirs`, which returns the `comms` key per layout. A bare `.aw/records/comms`-then-`.agents/comms` existence probe picks the WRONG lane in a repo carrying both trees, which `engine.detect_split_brain_layout` exists because it happens. This plan calls the same two functions child 01 does and reimplements no probe (F-9).
- CHILD 01 SHIPS THE SYMBOLS THIS PLAN MUST REUSE, and they are named here so E-01/E-03 cite symbols rather than prose: `comms_broker.url_policy_refusal(url)` (the loopback plus scheme policy), a `RefusingRedirectHandler`-style opener that re-checks every redirect target, `--broker-id` as the ack `by` identity (never derived from a message), and `BROKER_ACK_STATES`. Re-verified: `comms.BROKER_ACK_STATES` contains `agent-not-running` and `agent-not-responding`, and `comms.ack_writer_for` returns `broker` for both, so E-03's two failure states are legitimately broker-authored under the spec's closed enum.
- A DESCRIPTOR IS UNTRUSTED INPUT. `untracked/registry/` is gitignored and locally writable, so a descriptor's `url` is a value flowing from an unvetted file into an outbound request; the spec's "Untrusted-input stance (mandatory)" is the contract, and the guard is child 01's URL policy rather than anything new (F-4).

## Findings

- F-1 (re-measured 2026-09-24, OpenCode 1.18.32 `/doc`): `/global/health` 200 schema is `{"healthy": true, "version": <string>}`; `/path` 200 schema has required `directory` and `worktree`. These give a liveness check and an identity check without reading any session content.
- F-2: mDNS is real (`opencode serve --mdns`, "enable mDNS service discovery (defaults hostname to 0.0.0.0)") but enabling it binds all interfaces, which contradicts child 01's loopback-only rule, and browsing needs a client this repo does not have (`import zeroconf` raises `ModuleNotFoundError`). The research report `j2000q` also records "Cross-instance reachability and mDNS behavior remain unverified." So mDNS is deferred and the filesystem descriptor, which the backlog item names as the fallback, becomes the v1 mechanism.
- F-3: `opencode attach <url>` is a CLIENT connecting to a server, not a discovery source; it is useful to the human (start `opencode serve --port N`, then `attach`) and to the descriptor (the URL is known), but the broker does not call it.

Findings F-4 onward were added by `/plan-review` on 2026-09-25 at HEAD `6d61a387`. F-1's two route schemas, F-2's `import zeroconf` failure and the stdlib-only dependency claim were all re-verified and HOLD; `comms.BROKER_ACK_STATES` really does contain both states E-03 uses and `comms.ack_writer_for` returns `broker` for each.

- F-4 NEW, THE TRUST BOUNDARY: a descriptor is UNTRUSTED INPUT and E-03 opened two unguarded sockets to it. `untracked/registry/` is a gitignored local directory, so any local process may write `<agent>.json` naming any loopback URL and port, including an agent that has just processed a hostile inbox message (the spec's "Untrusted-input stance" says a payload is untrusted and sender identity is self-asserted). Child 01 guards its ONE outbound call with `url_policy_refusal` plus a `RefusingRedirectHandler` that re-checks EVERY redirect target, and `nomhl1`'s own review recorded that "a redirect to a non-loopback target refused ... is the one a bare entry check misses". E-03 as authored named neither symbol, saying only "using the same check child 01 added" in E-01 and nothing at all in E-03, so the registry path would have made two NEW outbound calls from a disk-supplied URL outside the policy child 01 exists to enforce. It also trusted registration-time validation for a file that may have been replaced since.
- F-5 NEW, THE WORKTREE AMBIGUITY: `/path` returns BOTH `directory` and `worktree` (F-1 records both required keys) and E-03 compared only `directory`, with no statement of why. That matters here specifically: measured at review, THREE live worktrees of this repository exist simultaneously (`git worktree list`), all sharing one `--git-common-dir`, and each carries its own `.aw/records/comms` lane. So `worktree` is NOT a discriminator between two lanes of the same repo while `directory` is, and a reader cannot tell from the plan whether the choice was reasoned or accidental. Comparing the wrong key would let a broker in one lane nudge the OpenCode instance of another lane, which is exactly the cross-tree confusion the check exists to prevent.
- F-6 NEW, THE ACK HAS NO MESSAGE AND NO IDEMPOTENCE: E-04 says the broker "writes the resulting failure state as the broker ack" without saying which message it attaches to or how often. `comms.ack_filename(msg_id, from_agent, state)` REQUIRES a msg-id, and a resolution failure is a property of the target rather than of one message, so the item as written does not determine what file to create. And with child 01's `--interval` default of 10 seconds, a target down for one hour would rewrite the same ack about 360 times. Child 01 already pins the equivalent invariant for its own ack ("a second `scan_once` on the same not-yet-due message does NOT rewrite the `scheduled` ack (compare `st_mtime_ns`)"), so an unpinned rewrite here would be a regression against a sibling plan's established rule.
- F-7 The `untracked/registry/` lane is gitignored in BOTH layouts, verified rather than assumed. Probed in this worktree: `git check-ignore -v .aw/records/comms/untracked/registry/probe.json` matches `.aw/.gitignore:6: records/*/untracked/`. The legacy `.agents/comms/` layout is covered by its own nested `.gitignore` per the spec's Gitignore paragraph, so E-01's parenthetical is correct for the canonical layout and the legacy case is also covered.
- F-8 The registry is PER-REPO-ROOT, which bounds the `<agent>.json` key collision the flat naming would otherwise invite. Each of the three live worktrees has its own `.aw/records/comms`, so two lanes running an agent of the same name do not overwrite each other's descriptor; the collision would only arise for two instances of the same agent name serving the SAME tree, which the `directory` check then resolves to whichever is live. No change needed; recorded so a later reader does not "fix" the flat naming.
- F-9 Child 01's contract is richer than this plan's references to it suggest, and the gaps are worth naming so E-05 wires against the real thing: `nomhl1` ships `url_policy_refusal` (E-09), a `RefusingRedirectHandler`-style opener, a `--broker-id` flag whose value is the ack `by` identity (deliberately NOT derived from any message), and a `comms_dir` resolution via `engine.resolve_target_layout` plus `engine._record_scaffold_dirs` rather than an existence probe. This plan's `Project conventions` bullet describes the comms dir as chosen by a `.aw/records/comms`-then-`.agents/comms` rule, which is the formulation child 01's review explicitly corrected.

## Proposed changes (ordered, validatable)

1. Descriptor schema and validator reusing child 01's URL policy (E-01).
2. `register`/`unregister` (E-02).
3. Verified resolution through the same policy and redirect-refusing opener (E-03), with the `/path` key choice stated and justified (E-04), wired into `run` (E-05) with a defined and idempotent failure ack (E-06).
4. Tests (E-07) plus the four trust-boundary and idempotence cases (E-08), spec (E-09), bare suite (E-10).

ONE URL POLICY, TWO CALL SITES, stated once so the two cannot drift. Child 01 owns `url_policy_refusal` and the redirect-refusing opener; this plan adds a SECOND place a URL enters the module (a descriptor read from disk) and TWO MORE outbound calls (`/global/health`, `/path`). Every one of them goes through the same predicate and the same opener. Do NOT re-encode the loopback set inside `validate_descriptor`, and do NOT open the verification GETs with a bare `urllib` opener: both are how one policy becomes two, and the redirect half is the part a bare entry check misses (F-4).

WHICH `/path` KEY DECIDES, and why it is not obvious. `directory` is authoritative; `worktree` is recorded and not compared. In this repository three worktrees of the same repo run simultaneously and share one `worktree` value while each has its own `directory` and its own comms lane, so comparing `worktree` would let a broker in one lane nudge another lane's instance (F-5). A reader who later "simplifies" the check to whichever key is handy reintroduces exactly that, which is why E-04 puts the reason in the docstring rather than only here.

WHAT A FAILURE ACK ATTACHES TO. An ack is keyed on a message, a resolution failure is a property of the target, and the reconciliation is: write it once per ELIGIBLE message the scan would have nudged, and never rewrite an ack already in that state for that msg-id (F-6). The second half matters because child 01 polls every 10 seconds by default and already pins the same non-rewrite invariant for its `scheduled` ack.

## Deferred / out of scope (with reason)

- mDNS browsing of `opencode serve --mdns` instances: needs a non-stdlib client and binds 0.0.0.0 (F-2).
  - Carrier-Declined: Conflicts with the loopback-only rule and adds a dependency; revisit only if cross-box delivery is scoped.
- Cross-box delivery and reachability.
  - Carrier-Evidence: .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md
- Automatic self-registration by an OpenCode instance (plugin or startup hook).
  - Carrier-Declined: Needs an OpenCode plugin surface this repo does not ship; explicit registration keeps the feature opt-in.
- Pruning stale descriptors automatically.
  - Carrier-Declined: The broker must not delete another party's files; `unregister` is the owner's act.
- AUTHENTICATING THE DESCRIPTOR'S WRITER. Any local process may write `untracked/registry/<agent>.json`, and this plan does not establish who wrote one; it establishes only that the URL it names is loopback, reachable, healthy, and serving THIS tree (F-4). Not closed here because the only ways to close it are a signature scheme or an OS-level permission model, both of which are far larger than a v1 registry and neither of which child 01's threat model assumes. The residual risk is bounded and worth stating plainly: a hostile descriptor can at most redirect a CONTENT-FREE `NUDGE` to another loopback server that is also serving this exact repo root, which is a denial or misdirection of a nudge and never a payload disclosure, because the broker is payload-blind by child 01's invariant.
  - Carrier-Declined: no obligation is outstanding on anybody, because the same trust level already governs every other file in `untracked/` (the spec's own "Untrusted-input stance" treats locally-dropped content as unvetted by design) and the bounded consequence is a lost nudge; a signature scheme would be a new spec decision, not deferred work from this plan.
- `pid` LIVENESS (`os.kill(pid, 0)`), recorded because OQ-01 asks it and the default answer is "record but do not rely on".
  - Carrier-Declined: OQ-01 states the reasoning (a pid can be reused and a wrapper may register on behalf of another process), and the health plus `directory` check is authoritative, so there is no outstanding work unless the maintainer overrides the default.

## Scope check

- Over-scope: none. Only `comms_broker.py` from child 01 is edited.
- Under-scope, CLOSED at review: the plan named neither `url_policy_refusal` nor the redirect-refusing opener for its TWO NEW outbound calls, which is the whole trust boundary (F-4); E-03 and E-08 now own it. The `/path` comparison used one of two required keys with no stated reason (F-5); E-04 owns it. And the failure ack had no message and no idempotence rule (F-6); E-06 owns it.
- Under-scope: none further known. If child 01 was re-scoped at its E-01 spike, re-read its executed record before starting and adjust E-05 to its actual `run` signature. In particular re-read the SYMBOL NAMES: this plan cites `url_policy_refusal`, the redirect-refusing opener, `--broker-id` and `BROKER_ACK_STATES` from child 01's reviewed text, and a rename during execution would leave those citations stale.
- EXPLICITLY NOT IN SCOPE: the message envelope and the ack enum (`comms.BROKER_ACK_STATES` is consumed, never extended); `comms.is_filename_safe`, `ack_filename`, `validate_ack`, `ack_writer_for` (reused, never forked); child 01's `deliver`, `scan_once`, `url_policy_refusal` and `--broker-id` BEHAVIOR (this plan calls them and changes none); `engine.resolve_target_layout` and `_record_scaffold_dirs`; the shard or gitignore layout; `pyproject.toml` dependencies (stdlib only, no new dependency); any `.agents/` legacy tree migration; and the spec's `- Status:` and `## Workflow history` (body-only amendment, history via `aw specs note`).

## Required tests / validation

- `tests/test_comms_broker_registry.py` targeted, plus a mutation run showing the directory-mismatch test FAILS.
- The four trust-boundary and idempotence cases of E-08, with the fixture's ZERO-request evidence for the two refusal cases (a failure state alone cannot distinguish "refused before connecting" from "connected then failed").
- Child 01's `tests/test_comms_broker.py` shown still green, since this plan edits the module that file covers.
- `python3 -m pytest` bare with the summary line pasted.

KNOWN PRE-EXISTING SUITE FAILURE, recorded so it is not mistaken for damage this plan did: at review HEAD `6d61a387` the bare suite reports `1 failed, 1949 passed, 1 skipped`, the single failure being `tests/test_terminal_status_vocabulary.py::TestExecutionSuccessStatesNarrowingAndBlastRadius::test_blast_radius_zero_across_pending_plans`, which fails because pending plan `je74a0` references the stranded prerequisite `72qlya`. It reproduces at `25eb9a08`, has nothing to do with comms, and V-10 must name it as pre-existing rather than treating a non-zero failure count as this plan's regression.

## Spec / documentation sync

- Amends `.aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md` (declared in `- Scope-Paths:`), because its Deferred list names filesystem discovery and would be false once this ships.

## Open questions

### OQ-01: Should a descriptor also be matched on `pid` liveness (`os.kill(pid, 0)`)?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: record `pid` but do not rely on it; the health plus directory check is authoritative because a pid can be reused and a wrapper may register on behalf of another process. Reviewed and the default stands on a stronger reason than pid reuse alone: `os.kill(pid, 0)` answers "is SOME process alive with that id", which is strictly weaker than what the two HTTP calls already prove (a server is answering AND it is serving this exact tree), so a pid check could only ever turn an already-refused case into a differently-refused case, never accept something the HTTP checks reject. Adding it would also invite a reader to treat a live pid as sufficient and skip a verification call.
- Carrier-Declined: nothing is outstanding on anybody. The plan ships the authoritative check (health plus `directory`) and the residual question would only ADD a weaker signal alongside it; adopting it is a maintainer preference with no defect behind it, and the `pid` field is recorded in the descriptor either way so a later change needs no migration.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_comms_broker_registry.py -k descriptor -v` showing PASSED for valid, non-loopback-rejected, headless-without-session-rejected and unsafe-name-rejected.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a `register` run into a tmp repo followed by `ls untracked/registry/` showing `<agent>.json`, then `unregister` and the empty listing; and an invalid `register` exiting 2 (`echo $?`).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the `-k resolve` run showing PASSED for directory-mismatch -> `agent-not-responding`, missing -> `agent-not-running`, and stale descriptor still present afterwards. PLUS the trust-boundary proof, which is the claim this item is most exposed to faking: paste the SOURCE of `resolve_target` showing `url_policy_refusal` called before any socket is opened and the two GETs using child 01's redirect-refusing opener, and paste a run showing a non-loopback descriptor refused with the fixture recording ZERO requests. A failure state alone does not satisfy this item: an unguarded resolver that connects and then fails returns the same state as a guarded one that never connects.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `resolve_target`'s docstring showing it names BOTH `/path` keys and states which one decides and why, plus the `-k worktree` run showing a fixture that serves a SIBLING worktree's `directory` with the SAME `worktree` value is REFUSED. The sibling case is the point: a test that only varies `directory` passes under a buggy implementation that compares `worktree`, so the same-`worktree` fixture is what makes the assertion mean anything.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the `-k explicit_url` run showing PASSED (registry not consulted when `--target-url` is given) and child 01's `python3 -m pytest -o addopts="" tests/test_comms_broker.py` summary still green.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the `-k idempot` (or equivalent) run showing PASSED, with BOTH `st_mtime_ns` values printed and EQUAL across two consecutive scans against a down target, and paste `ls untracked/acks/` showing exactly one ack file per eligible message rather than one per scan. Also paste the ack filename, showing its msg-id is a real message's stem (E-06's rule that a failure ack attaches to an eligible message, never to a synthesized or absent id).
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the full `python3 -m pytest -o addopts="" tests/test_comms_broker_registry.py` summary, then the same run with the `directory` comparison locally mutated to always pass, showing the directory-mismatch test FAILED; revert and show the file matches the intended version (an empty `git diff` for that path).
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste the run of all four cases PASSING, and for (a) and (b) paste the fixture's recorded request count showing ZERO requests reached it, which is the only evidence that distinguishes "refused before connecting" from "connected and then failed". For (c) paste the descriptor's content before and after the on-disk replacement, and for (d) both `st_mtime_ns` values.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste `git diff -- .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md` showing the registry subsection, mDNS still deferred, and the note line.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste the bare `python3 -m pytest` summary line (`N passed`, 0 failed).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Ten items, one concern: resolving a broker target by agent name from a verified local descriptor. The count grew from seven at review through three splits, each because the added work has its own independent test surface and its own failure mode. E-04 separates the `/path` key decision (verified by a same-`worktree` sibling fixture) from the resolver itself. E-06 separates the failure ack's identity and idempotence (verified by two `st_mtime_ns` values) from wiring `run`. E-08 separates the four trust-boundary and idempotence cases (verified by the fixture's request count, which the happy-path tests never inspect) from the main test file. No item introduces a second concern.

WHAT A HUMAN IS APPROVING. An OPT-IN, same-box convenience: an operator writes a descriptor, and the broker resolves a target by name instead of by hand-typed URL. Four things to weigh. FIRST, this adds a new UNTRUSTED INPUT to the module: `untracked/registry/` is gitignored and locally writable, so the URL the broker verifies now comes from a file rather than from the operator's command line, and the guard is child 01's existing loopback plus redirect policy applied to two NEW outbound calls (F-4). SECOND, the residual risk is bounded and worth stating: a hostile descriptor can at most misdirect a CONTENT-FREE nudge to another loopback server that is also serving this exact repo root; it cannot disclose a payload, because child 01's payload-blind invariant means the broker never reads one. Authenticating the descriptor's WRITER is explicitly not attempted (see Deferred). THIRD, nothing is installed, nothing auto-starts, and no dependency is added (stdlib only, `pyproject.toml` declares `filelock>=3` alone). FOURTH, an approved-and-executed `nomhl1` is a hard prerequisite: `agent_workflows/comms_broker.py` does not exist at review time, so this plan's every citation of `url_policy_refusal`, the redirect-refusing opener, `--broker-id` and `run`'s signature is a citation of child 01's REVIEWED TEXT and must be re-read against its executed record.

SCOPE FENCE (a DECLARATION for reconciliation, not a stop directive). The intended surface: in `agent_workflows/comms_broker.py`, a new `REGISTRY_SUBDIR` constant, `validate_descriptor`, the `register`/`unregister` subcommands, `resolve_target`, and the `--target-agent` branch of `run` plus its failure-ack write; `tests/test_comms_broker_registry.py` is new; the comms spec gets a body-only "Broker target registry (optional)" subsection and one edited Deferred bullet. The EXPLICITLY NOT IN SCOPE list is in the Scope check section and is part of this fence. An out-of-scope edit is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

HONESTY RULE (hard MUST). Paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. This plan is most exposed to faking on V-03 and V-08, because an unguarded resolver that connects and THEN fails returns the same ack state as a guarded one that never connects, so only the fixture's recorded request count distinguishes them; on V-04, because a mismatch test that varies only `directory` passes under an implementation that wrongly compares `worktree`, which is why the sibling fixture must share the `worktree` value; and on V-06, because an ack that is rewritten every scan still leaves exactly one file on disk, so only the `st_mtime_ns` pair detects it.

STOP CONDITIONS (genuinely unsafe, distinct from the scope fence). Stop and report if: `nomhl1` is not in `executed/`, since this plan edits a module that does not otherwise exist; `comms_broker.url_policy_refusal` or the redirect-refusing opener is absent under any name, since E-03's trust boundary has no fallback and re-encoding the policy here is explicitly forbidden; or `comms.BROKER_ACK_STATES` no longer contains both `agent-not-running` and `agent-not-responding`, or `comms.ack_writer_for` no longer returns `broker` for them, since E-03's failure states would then be unauthorized under the spec's closed enum.

OQ-01 is `Blocking: no` with a stated default and a declined carrier. This plan is `to-review`, carries `- Item-Dependencies: executed:nomhl1`, and requires explicit human approval before execution. THE EXECUTOR NEVER PROBES A HUMAN'S LIVE OPENCODE INSTANCE and no test shells out to `opencode`: the suite uses a loopback `http.server` fixture so it stays hermetic on a machine with no OpenCode installed. Commit only the `- Scope-Paths:` via `aw commit ex539u -- <paths>`, never `git add -A`, and never push. This plan carries NO `- Blocks-Release:` and neither does backlog `lbhmi3`, so no release gate is owed or inherited; close `lbhmi3` only after this plan reaches `executed/`. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is UNCONDITIONALLY owed, but under `aw oc run`/`aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-10 carry pasted evidence.
