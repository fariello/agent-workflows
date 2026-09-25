# IPD: Comms broker discovery registry of live OpenCode targets (filesystem descriptor, mDNS optional)

- Date: 2026-09-24
- Kind: child
- Concern: Child 01 (`nomhl1`) makes the broker take an explicit `--target-url`, because an OpenCode instance's server port is ephemeral by default (`opencode serve --help`: "--port ... [default: 0]") and nothing records which instance serves which agent. Backlog `lbhmi3` ("agent-comms IPD 4: broker discovery/registry of live targets (mDNS/attach + filesystem fallback)") closes that gap. The spec's Deferred list names it: "Discovery/registry (mDNS / attach / filesystem descriptor), cross-instance reachability."
- Scope: IN: a same-box FILESYSTEM registry. An opted-in instance's operator (or a wrapper) writes a small JSON descriptor into `untracked/registry/` via `python3 -m agent_workflows.comms_broker register --agent <proj.agent> --url <loopback url> --mode tui|headless [--session <id>]`; the broker gains `--target-agent` resolution from that registry, verifying liveness with `GET /global/health` and that `GET /path` `directory` matches the repo root before nudging. Stale descriptors are skipped and reported, never deleted by the broker. OUT: mDNS browsing (no stdlib mDNS client; see Deferred), cross-box reachability, auto-registration from inside OpenCode (would need a plugin), any change to the envelope or ack enum.
- Scope-Paths: agent_workflows/comms_broker.py, tests/test_comms_broker_registry.py, .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md
- Item-Dependencies: executed:nomhl1
- Status: to-review
- Work-Kind: feature
- Priority: low
- From-Backlog: lbhmi3
- Set: commsbroker
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: ex539u

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog lbhmi3; re-measured the OpenCode 1.18.32 `/doc` for the liveness and identity routes (`/global/health` returns `healthy`+`version`, `/path` returns `directory`) and confirmed no mDNS client is importable (`import zeroconf` fails; runtime deps are `filelock` only).

## Goal

Let the broker find a live, correct target by agent name on the same box instead of requiring a hand-typed URL, without adding a dependency and without trusting a descriptor it has not verified.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: registry

- [ ] E-01 Add `comms_broker.REGISTRY_SUBDIR = "registry"` under the comms `untracked/` lane (gitignored already, because the canonical layout ignores `records/*/untracked/` per the spec's Gitignore section) and a descriptor schema `{"agent", "url", "mode", "session", "pid", "registered_at"}` with `validate_descriptor(obj)` returning a problem list. `agent` must pass `comms.is_filename_safe`, `url` must be loopback http(s) using the same check child 01 added, `mode` in `tui|headless`, `session` required when `mode == "headless"`.
  - Depends on: none
  - Expected outcome: a pure validator; no I/O.
  - Execution state: pending
- [ ] E-02 Add the `register` and `unregister` subcommands: write `untracked/registry/<agent>.json` atomically (temp file then `os.replace`) after validation, and remove it on `unregister`. Registration is always an explicit human or wrapper act; nothing registers implicitly.
  - Depends on: E-01
  - Expected outcome: `register` creates one valid descriptor file; `unregister` removes it; an invalid descriptor exits 2 and writes nothing.
  - Execution state: pending
- [ ] E-03 Add `comms_broker.resolve_target(comms_dir, agent, repo_root, *, opener)`: load the descriptor, then `GET <url>/global/health` (must return `"healthy": true`) and `GET <url>/path` (its `directory` must equal `repo_root` after `os.path.realpath`). Return the descriptor on success, or an ack state on failure: missing descriptor or refused connection -> `agent-not-running`; unhealthy, timeout or directory mismatch -> `agent-not-responding`. Never deletes a stale descriptor.
  - Depends on: E-02
  - Expected outcome: a resolver that refuses an instance serving a different directory.
  - Execution state: pending
- [ ] E-04 Wire `run`: `--target-url` stays accepted; when it is omitted, the broker calls `resolve_target` for `--target-agent` on every scan (so a restarted instance with a new port is picked up after it re-registers) and writes the resulting failure state as the broker ack instead of attempting delivery.
  - Depends on: E-03
  - Expected outcome: explicit URL behaves exactly as in child 01; registry path used only when no URL is given.
  - Execution state: pending

### Task group 2: tests, spec, suite

- [ ] E-05 Write `tests/test_comms_broker_registry.py` with a loopback `http.server` fixture serving `/global/health` and `/path`: valid registration round-trip; invalid descriptor rejected (non-loopback URL, headless without session, unsafe agent name); directory mismatch -> `agent-not-responding` and no nudge request; missing descriptor -> `agent-not-running`; stale descriptor left in place; explicit `--target-url` bypasses the registry.
  - Depends on: E-04
  - Expected outcome: all pass; the directory-mismatch test fails under the mutation named in V.
  - Execution state: pending
- [ ] E-06 Amend the spec: add a "Broker target registry (optional)" subsection (descriptor path and schema, the two verification calls, stale handling, mDNS deferred) and move filesystem discovery out of the Deferred bullet, leaving mDNS and cross-instance reachability deferred; append a `## Workflow history` note line.
  - Depends on: E-05
  - Expected outcome: the spec matches shipped behavior.
  - Execution state: pending
- [ ] E-07 Run the bare suite `python3 -m pytest`.
  - Depends on: E-06
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Runtime dependencies are `dependencies = ["filelock>=3"]` (`pyproject.toml`); stdlib only.
- The comms directory is chosen per layout in `engine` (`comms_dir = ".aw/records/comms"` for the aw layout, `".agents/comms"` for legacy); child 01's entry point already follows it.

## Findings

- F-1 (re-measured 2026-09-24, OpenCode 1.18.32 `/doc`): `/global/health` 200 schema is `{"healthy": true, "version": <string>}`; `/path` 200 schema has required `directory` and `worktree`. These give a liveness check and an identity check without reading any session content.
- F-2: mDNS is real (`opencode serve --mdns`, "enable mDNS service discovery (defaults hostname to 0.0.0.0)") but enabling it binds all interfaces, which contradicts child 01's loopback-only rule, and browsing needs a client this repo does not have (`import zeroconf` raises `ModuleNotFoundError`). The research report `j2000q` also records "Cross-instance reachability and mDNS behavior remain unverified." So mDNS is deferred and the filesystem descriptor, which the backlog item names as the fallback, becomes the v1 mechanism.
- F-3: `opencode attach <url>` is a CLIENT connecting to a server, not a discovery source; it is useful to the human (start `opencode serve --port N`, then `attach`) and to the descriptor (the URL is known), but the broker does not call it.

## Proposed changes (ordered, validatable)

1. Descriptor schema and validator (E-01).
2. `register`/`unregister` (E-02).
3. Verified resolution (E-03), wired into `run` (E-04).
4. Tests (E-05), spec (E-06), bare suite (E-07).

## Deferred / out of scope (with reason)

- mDNS browsing of `opencode serve --mdns` instances: needs a non-stdlib client and binds 0.0.0.0 (F-2).
  - Carrier-Declined: Conflicts with the loopback-only rule and adds a dependency; revisit only if cross-box delivery is scoped.
- Cross-box delivery and reachability.
  - Carrier-Evidence: .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md
- Automatic self-registration by an OpenCode instance (plugin or startup hook).
  - Carrier-Declined: Needs an OpenCode plugin surface this repo does not ship; explicit registration keeps the feature opt-in.
- Pruning stale descriptors automatically.
  - Carrier-Declined: The broker must not delete another party's files; `unregister` is the owner's act.

## Scope check

- Over-scope: none. Only `comms_broker.py` from child 01 is edited.
- Under-scope: none known. If child 01 was re-scoped at its E-01 spike, re-read its executed record before starting and adjust E-04 to its actual `run` signature.

## Required tests / validation

- `tests/test_comms_broker_registry.py` targeted, plus a mutation run showing the directory-mismatch test FAILS.
- `python3 -m pytest` bare with the summary line pasted.

## Spec / documentation sync

- Amends `.aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md` (declared in `- Scope-Paths:`), because its Deferred list names filesystem discovery and would be false once this ships.

## Open questions

### OQ-01: Should a descriptor also be matched on `pid` liveness (`os.kill(pid, 0)`)?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: record `pid` but do not rely on it; the health plus directory check is authoritative because a pid can be reused and a wrapper may register on behalf of another process.

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
  - Required evidence: paste the `-k resolve` run showing PASSED for directory-mismatch -> `agent-not-responding`, missing -> `agent-not-running`, and stale descriptor still present afterwards.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the `-k explicit_url` run showing PASSED (registry not consulted when `--target-url` is given) and child 01's `python3 -m pytest -o addopts="" tests/test_comms_broker.py` summary still green.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the full `python3 -m pytest -o addopts="" tests/test_comms_broker_registry.py` summary, then the same run with the `directory` comparison locally mutated to always pass, showing the directory-mismatch test FAILED; revert and show the file matches the intended version.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `git diff -- .aw/records/specs/implemented/20260715-1722-01-agent-comms-convention.spec.md` showing the registry subsection, mDNS still deferred, and the note line.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the bare `python3 -m pytest` summary line (`N passed`, 0 failed).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OQ-01 is `Blocking: no` with a stated default. This plan is `to-review`, depends on `nomhl1` being executed, and requires explicit human approval before execution. The executor never probes a human's live OpenCode instance (tests use a local fixture server), commits only the `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never pushes, and pastes actual runner output. On completion `aw ipd lint --phase pre-transition` must conform before the terminal transition, owned by the runner in a managed lane and otherwise by `aw ipd finalize`.
