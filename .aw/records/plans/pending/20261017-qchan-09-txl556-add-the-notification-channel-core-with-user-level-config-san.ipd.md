# IPD: Add the notification channel core with user-level config, sanitized terse output and a webhook hook

- Date: 2026-10-17
- Kind: child
- Concern: A human away from the terminal still never learns a question is waiting. Spec `6kwd2e` R10 (amended 2026-10-17) defines the channel layer: one adapter interface, opt-in user-level configuration with no tracked secrets, sanitized outbound text with a terse default, sender verification, a user-level routing registry, one notification per park and an acknowledgement per consumed answer, and a notify-only generic webhook and command hook (R10.8b) that covers ntfy, Microsoft Teams and Google Chat incoming webhooks without per-service code.
- Scope: IN: `agent_workflows/notify/` package with the `Channel` protocol (`capabilities`, `send`, `receive`, `verify`, `ack`, `health`), user-level config `<AW_HOME>/notify.json` (0600 on POSIX, user-only ACL attempt on Windows, env-var overrides), a tracked-policy reader that may only forbid channels or force terse, the outbound builder (leak sanitizer then truncate), terse mode, the user-level registry for channel message ids and option tokens, the dispatcher hooked into the park point (Order 02) and the consume point (Order 04), and the `webhook` and `command` channels. OUT: Telegram (Order 10), setup commands (Order 11).
- Scope-Paths: agent_workflows/notify/__init__.py, agent_workflows/notify/core.py, agent_workflows/notify/config.py, agent_workflows/notify/registry.py, agent_workflows/notify/webhook.py, agent_workflows/runner_shared.py, agent_workflows/question_inbox.py, tests/test_notify_core.py
- Item-Dependencies: executed:j0ufrj
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 9
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: txl556

## Workflow history
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Notify the human off-machine when a question parks, safely and with zero setup beyond one URL or command, and give the two-way channels a shared core (spec `6kwd2e` R10.1-R10.4, R10.7, R10.8b).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: config and policy

- [ ] E-01 Add `agent_workflows/notify/config.py`: load `<AW_HOME>/notify.json` (`project_context.get_default_aw_home`) with per-channel entries (`enabled`, `mode` terse|full, channel settings) and env overrides (`AW_NOTIFY_WEBHOOK_URL`, `AW_NOTIFY_COMMAND`); create it with mode 0600 on POSIX and a best-effort user-only ACL on Windows (`icacls`), warning if broader permissions are found; ignore and WARN on any channel secret found in tracked `.aw/config/` (A48); read tracked `.aw/config/project.json` key `notify_policy` (`forbid` | `terse-only`) as a ceiling, never as enablement (R10.2).
  - Depends on: none
  - Expected outcome: a fresh config file is created 0600; a secret in tracked config is ignored with a warning; `notify_policy: forbid` disables every channel even when the user enabled one.
  - Execution state: pending

### Task group 2: core and registry

- [ ] E-02 Add `notify/core.py`: the `Channel` protocol and dataclasses (`OutboundQuestion`, `Receipt`, `InboundEvent`, `Caps`, `Health`); `build_outbound(question, mode, caps)` that runs text through the package leak sanitizer (`leak_sanitizer.build_ruleset` + redaction used by `aw sanitize`) BEFORE truncating to `caps.max_text`, and in terse mode emits only `run <run-id>: N question(s) waiting; answer with aw runs answer <run-id>` (R10.3, R10.4, default terse for new channels). Add `notify/registry.py`: a user-level JSON registry under `<AW_HOME>/notify/` guarded by `filelock`, mapping (channel, channel message id or option token) to (run dir, question id, option, artifact hash), with expiry of entries whose question is answered or whose run directory is gone. Inbound events are deduplicated by (channel, event id).
  - Depends on: E-01
  - Expected outcome: a question containing an absolute home path is sent with it redacted; terse output contains no question text; registry lookups survive a process restart and expire answered entries (A49).
  - Execution state: pending

- [ ] E-03 Hook the dispatcher into the run: at park (Order 02/03 write point) call `notify.core.on_parked(run_dir, questions)` once per newly parked batch; at consumption (Order 04) call `on_consumed` to send a short `answered via <channel>` acknowledgement; never re-notify the same question on later checkpoints (`notified` flag in the question file); every channel exception is caught and recorded as a `notify-failed` event and never fails the run (R10.7, R10.6 last sentence).
  - Depends on: E-02
  - Expected outcome: two checkpoints with the same parked question send one notification; consuming its answer sends one acknowledgement; a channel that raises yields an event and an unaffected run (A55).
  - Execution state: pending

### Task group 3: notify-only channels

- [ ] E-04 Add `notify/webhook.py` with two channels. `webhook`: POST the sanitized JSON body (`aw.notify/v1`: run id, count, and in full mode each question's text, options and the answer command) to a configured URL with `urllib.request`, 10 s timeout, honoring `HTTPS_PROXY`; optional ntfy-style `Title`/`Tags` headers when `format: ntfy` is set. `command`: run a configured argv (never a shell string) with the JSON on stdin and a 30 s timeout. Neither implements `receive` and neither writes `answers/` (A53).
  - Depends on: E-03
  - Expected outcome: against a local HTTP test server the webhook receives the sanitized body; a command receives it on stdin; neither creates any answer file.
  - Execution state: pending

### Task group 4: tests

- [ ] E-05 Add `tests/test_notify_core.py` covering config permissions, tracked-secret warning, policy ceiling, sanitization and terse mode, registry, once-per-park and acknowledgement, failure isolation, and both notify-only channels against a local `http.server` and a fixture command.
  - Depends on: E-04
  - Expected outcome: the module passes on Linux; Windows ACL behavior is asserted only where the platform supports it (skipped elsewhere with a stated reason).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `filelock` is the only runtime dependency; nothing new is added (research `kdg4uz`, `js5p5k`).
- User-level state lives under `AW_HOME` (`project_context.get_default_aw_home`).
- Secrets never in tracked config (AGENTS.md leak-sanitizer rules; spec `6kwd2e` R10.2).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- No notification exists anywhere in the package (research `xjsc9k`).
- ntfy, Teams Workflows and Google Chat all accept an incoming HTTPS POST, so one webhook channel covers them (research `kdg4uz`, `js5p5k`).

## Proposed changes (ordered, validatable)

1. E-01 config/policy. 2. E-02 core + registry. 3. E-03 run hooks. 4. E-04 webhook + command. 5. E-05 tests.

## Deferred / out of scope (with reason)

- Telegram two-way: Order 10.
  - Carrier: qrup8m
- `aw notify setup|test|status|listen`: Order 11.
  - Carrier: mrlblc
- Signal: backlog `szjsgj` (parked).
  - Carrier-Declined: not shipped by decision (spec `6kwd2e` R10.10); a possible later channel is recorded as parked backlog `szjsgj`, which is a maybe, not committed work

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_notify_core.py` and the routine gate.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R10.1-R10.4, R10.7, R10.8b as amended.

## Open questions

### OQ-01: Use Apprise for notify-only services?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED: no. It is a large third-party dependency and the package keeps `filelock` as its only runtime dependency; a generic webhook plus a command hook reaches the same services (users who want Apprise can point the command hook at its CLI).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `stat -c %a` of the created config, the warning for a tracked secret, and the policy-ceiling test output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the outbound text for a question containing a home path (full and terse modes) and a registry round-trip across two processes.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the event log of a scripted run showing one `notify-sent` per park, one acknowledgement after consumption, and a `notify-failed` event with the run still exiting normally (E-03's hooks).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the local test server's received body and the fixture command's captured stdin, and `ls answers/` showing nothing written.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
