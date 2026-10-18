# IPD: Add the notification channel core with user-level config, sanitized terse output and a webhook hook

- Date: 2026-10-17
- Kind: child
- Concern: A human away from the terminal still never learns a question is waiting. Spec `6kwd2e` R10 (amended 2026-10-17) defines the channel layer: one adapter interface, opt-in user-level configuration with no tracked secrets, sanitized outbound text with a terse default, sender verification, a user-level routing registry, one notification per park and an acknowledgement per consumed answer, and a notify-only generic webhook and command hook (R10.8b) that covers ntfy, Microsoft Teams and Google Chat incoming webhooks without per-service code.
- Scope: IN: `agent_workflows/notify/` package with the `Channel` protocol (`capabilities`, `send`, `receive`, `verify`, `ack`, `health`), user-level config `<AW_HOME>/notify.json` (0600 on POSIX, user-only ACL attempt on Windows, env-var overrides), a tracked-policy reader that may only forbid channels or force terse, the outbound builder (leak sanitizer then truncate), terse mode, the user-level registry for channel message ids and option tokens, the core's inbound routing entry point that later two-way channels call (`apply_inbound`), the dispatcher run at every dispatch checkpoint on both hosts (notifying newly parked questions from any source and acknowledging consumed or stale answers), and the `webhook` and `command` channels. OUT: Telegram (Order 10), setup commands and user docs (Order 11).
- Scope-Paths: agent_workflows/notify/__init__.py, agent_workflows/notify/core.py, agent_workflows/notify/config.py, agent_workflows/notify/registry.py, agent_workflows/notify/webhook.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_notify_core.py
- Item-Dependencies: executed:j0ufrj
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 9
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: txl556
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Notify the human off-machine when a question parks, safely and with zero setup beyond one URL or command, and give the two-way channels a shared core (spec `6kwd2e` R10.1-R10.4, R10.7, R10.8b).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: config and policy

- [x] E-01 Add `agent_workflows/notify/config.py`. USER CONFIG: `load_user_config()` reads `<AW_HOME>/notify.json` (`project_context.get_default_aw_home`) with per-channel entries (`enabled`, `mode` `terse`|`full`, channel settings) and NEVER creates it; `save_user_config(cfg)` (the writer Order 11 calls) writes atomically, creating the temp file with `os.open(..., O_CREAT|O_EXCL, 0o600)` on POSIX and, on Windows, applying a best-effort user-only ACL with `icacls` (argv form) and warning when that fails. On load, a POSIX file with any group or other permission bit (`st_mode & 0o077`) is re-chmodded to 0600 with a warning; if that fails the file is NOT read and every channel is off (fail closed, D-3). ENV: `AW_NOTIFY_WEBHOOK_URL` and `AW_NOTIFY_COMMAND` (a JSON argv list) configure their channel when set, always in `terse` mode unless `notify.json` sets `full` for it; a malformed env value is ignored with a warning. TRACKED CONFIG (R10.2): channel settings are NEVER read from `.aw/config/`; `tracked_secret_warnings(repo)` reports, without echoing values, any `notify` key or any key starting `notify_` other than `notify_policy` in the tracked `.aw/config/*.json` files, and the dispatcher prints each once per run. POLICY: `read_notify_policy(repo)` reads `.aw/config/project.json` key `notify_policy` (`forbid` | `terse-only`; absent means no ceiling) as a ceiling, never as enablement; it never raises, and an unreadable file or unrecognized value is treated as `forbid` with a warning (fail closed, D-2). `effective_channels(repo)` applies the ceiling to the user and env config. Malformed `notify.json` disables every channel with one warning; it never fails a run.
  - Depends on: none
  - Expected outcome: `save_user_config` creates the file with mode 0600; a 0644 file is tightened to 0600 on load with a warning; a `notify` key in tracked `project.json` produces a warning naming the file and key but not the value, and is not used; `notify_policy: forbid` and `notify_policy: bogus` both yield no effective channel even with one enabled; `terse-only` forces terse on a `full` channel (A48).
  - Execution state: performed

### Task group 2: core and registry

- [x] E-02 Add `notify/core.py`: the `Channel` protocol (`capabilities`, `send`, `receive`, `verify`, `ack`, `health`; notify-only channels implement `send` and `health` and declare `answer=False`) and dataclasses (`OutboundQuestion`, `OutboundBatch`, `Receipt`, `InboundEvent`, `Caps`, `Health`). `sanitize_outbound(text, repo) -> str` is the ONE function every outbound byte passes (R10.3), defined by what it guarantees rather than by a single helper, because the shipped `leak_sanitizer` rewrite covers only home paths (measured at review: a `ses_...` id survives `leak_sanitizer._rewrite_line`, and a `/srv/...` path is no `leak_sanitizer` finding at all): (1) strip ANSI and control characters except newline and tab; (2) rewrite home paths per line with `leak_sanitizer._rewrite_line`; (3) replace every remaining absolute path with `render_stream._redact_absolute_paths`; (4) replace every remaining match of `leak_sanitizer.build_ruleset(repo)` fail patterns (session ids, private repo names, the maintainer handle, user hints) with `<redacted>`; (5) re-scan with `leak_sanitizer.scan_text` and, if any fail finding remains, replace the whole field with `<redacted>`. Only THEN truncate to `caps.max_text` characters with a trailing `...`. `build_batch(run_id, questions, mode, caps, repo)`: in `terse` mode only `run <run-id>: N question(s) waiting; answer with aw runs answer <run-id>` (R10.4); in `full` mode additionally each question's sanitized text, options and `aw runs answer <run-id> <question_id>`. New channels default to `terse`.
  - Depends on: E-01
  - Expected outcome: a question containing a home path, a non-home absolute path, a `ses_` id and an ANSI escape is sent with all four removed in full mode; terse output contains no question text; truncation applies after redaction (A49).
  - Execution state: performed

- [x] E-06 Add `notify/registry.py`, the user-level routing registry two-way channels use (R10.1): JSON under `<AW_HOME>/notify/registry.json`, every read-modify-write under `filelock` on `<AW_HOME>/notify/registry.lock`, atomic writes. `register(channel, key, run_dir, question_id, option, artifact_hash)` where `key` is a channel message id or an option token; `lookup(channel, key)`; `seen_event(channel, event_id) -> bool` (records and reports duplicates, bounded to the newest 10000 ids per channel); `expire()` drops entries whose run directory is gone or whose question file is no longer `open`. Add `core.apply_inbound(channel, event) -> str` (`recorded`/`already`/`rejected`/`ignored`): drop a duplicate event (`ignored`), drop an event `channel.verify` returns None for (`ignored`, logged, no reply, R10.5), resolve the routing key, and write through `question_inbox.write_answer` (Order 03) with `channel=<name>`, `sender=<verified identity>`, `actor="human"`; the channel never writes `answers/` itself (R10.1, R9.2). Order 10 calls this rather than mapping events itself.
  - Depends on: E-02
  - Expected outcome: a registered key resolves in a second process after the first exits; a duplicate event id is `ignored` and writes nothing; an unverified sender writes nothing; a verified event writes exactly one answer through the shared writer; `expire()` removes entries for an answered question and for a deleted run directory.
  - Execution state: performed

- [x] E-03 Add the dispatcher `core.dispatch_checkpoint(run_dir, state, repo)` and call it on BOTH hosts at the top of `run_queue`, immediately after Order 04's `consume_answers` (so every park source is covered: emergent parks, re-parks, and Order 07's pre-flight routing, without hooking each writer), and once more immediately before the run summary is printed. It (1) reads `question_inbox.read_open_questions(run_dir)`, (2) sends, per effective channel, ONE batch containing every open question not yet recorded as sent to that channel, (3) records each sent `(channel, question_id)` in `<run_dir>/notify/sent.jsonl` and emits a `notify-sent` event (`channel`, count, no content), and (4) for each sent question whose `events.jsonl` now holds an `answer-consumed` or `answer-stale` event for that `question_id` (Order 04 E-01) and no acknowledgement in `sent.jsonl`, sends `answered via <answer channel>` or `answer not applied: the plan changed; ask again` respectively, once (R10.7). Question files are NEVER modified here: `question_inbox.set_question_status` stays their only status writer (Order 03 E-05). It runs under `--unattended` too (R9.7). Every channel exception or timeout is caught and recorded as a `notify-failed` event whose detail has the channel's secrets redacted (E-04), and never raises into the loop or changes an item (R10.6 last sentence). With no effective channel it does nothing and writes nothing.
  - Depends on: E-02
  - Expected outcome: two checkpoints with the same parked question send one batch; a pre-flight-routed question is notified at the first checkpoint; consuming its answer sends one acknowledgement and a stale answer sends the stale notice; a channel that raises yields a `notify-failed` event and an unaffected run; no question file changes; with no channel configured `<run_dir>/notify/` does not exist (A55).
  - Execution state: performed

### Task group 3: notify-only channels

- [x] E-04 Add `notify/webhook.py` with two channels (R10.8b). `webhook`: POST a batch to the configured URL with `urllib.request`, 10 s timeout, `HTTPS_PROXY` honored through the default proxy handler, redirects NOT followed (an opener whose redirect handler refuses), and an `https` URL required except for loopback hosts (`127.0.0.1`, `::1`, `localhost`), which tests use. `format` selects the body: `aw` (default, `aw.notify/v1` JSON: run id, count, and in full mode each question's text, options and answer command), `text` (`{"text": "<rendered message>"}`, the shape plain incoming chat webhooks accept), or `ntfy` (the rendered message as a plain-text body with `Title` and `Tags` headers). The URL is treated as a secret: events, warnings and `health()` show only its scheme and host. `command`: run a configured argv (never a shell string) with the `aw` JSON on stdin, 30 s timeout, output discarded, a nonzero exit or timeout reported as a failure. Neither implements `receive` and neither writes `answers/` (A53).
  - Depends on: E-03
  - Expected outcome: a local HTTP server on 127.0.0.1 receives the sanitized body in each of the three formats; an `http://` non-loopback URL is refused without a request; a 302 response is reported as a failure and not followed; a `notify-failed` event carries no URL path or query; a fixture command receives the JSON on stdin; no answer file is created.
  - Execution state: performed

### Task group 4: tests

- [x] E-05 Add `tests/test_notify_core.py` (marked `pytest.mark.core` so the new `notify` modules are covered by the routine gate, per CONTRIBUTING's core-tier rule) covering config permissions and tightening, env configuration, tracked-key warning, the policy ceiling including the malformed value, `sanitize_outbound` on each class of leak, terse and full batches, truncation after redaction, the registry across two processes, duplicate and unverified inbound events, once-per-park, acknowledgement and stale notice, failure isolation, and both notify-only channels against a local `http.server` and a fixture command. Every test runs under the conftest `AW_HOME` sandbox and makes no request off the loopback interface.
  - Depends on: E-04, E-06
  - Expected outcome: the module passes on Linux; Windows ACL behavior is asserted only where the platform supports it (skipped elsewhere with a stated reason); the routine gate passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `filelock` is the only runtime dependency (`pyproject.toml` `dependencies = ["filelock>=3"]`); nothing new is added.
- User-level state lives under `AW_HOME` (`project_context.get_default_aw_home`); tests run under the conftest `AW_HOME` sandbox.
- Tracked project policy is read directly from `.aw/config/project.json` with a never-raising reader, as `config.read_review_findings_gate` does; `project_schema.parse_portable_policy` preserves unknown keys, so `notify_policy` round-trips.
- Secrets never in tracked config (AGENTS.md leak-sanitizer rules; spec `6kwd2e` R10.2).
- Run events go through `runner_shared.append_jsonl` into `<run_dir>/events.jsonl`; question files change status only through `question_inbox.set_question_status` (Order 03 E-05).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- No notification exists anywhere in the package (research `xjsc9k`).
- ntfy, Teams Workflows and Google Chat all accept an incoming HTTPS POST (research `xjsc9k`, `kdg4uz`, `js5p5k`), but they expect different bodies, so E-04 offers body formats as data. Whether a Teams Workflow renders the `text` body depends on how the user built the workflow; that is not asserted here and belongs in Order 11's hand-test checklist.
- Measured at review: `leak_sanitizer._rewrite_line` rewrites home paths only; a `ses_` session id survives it, and `leak_sanitizer.build_ruleset(...)` has no rule for a non-home absolute path such as `/srv/...`, which `render_stream._redact_absolute_paths` does replace. So "run the leak sanitizer" needs the composed `sanitize_outbound` of E-02.
- An incoming-webhook URL embeds its credential (Teams, Google Chat and ntfy topics alike), so it is handled as a secret (E-04).

## Proposed changes (ordered, validatable)

1. E-01 config/policy. 2. E-02 core and outbound sanitizer. 3. E-06 registry and inbound routing. 4. E-03 checkpoint dispatcher. 5. E-04 webhook and command. 6. E-05 tests.

## Deferred / out of scope (with reason)

- Telegram two-way: Order 10. It calls `core.apply_inbound` (E-06) for inbound routing rather than mapping events to `write_answer` itself.
  - Carrier: qrup8m
- `aw notify setup|test|status|listen`, user docs and the CHANGELOG entry: Order 11.
  - Carrier: mrlblc
- Signal: backlog `szjsgj` (parked).
  - Carrier-Declined: not shipped by decision (spec `6kwd2e` R10.10); a possible later channel is recorded as parked backlog `szjsgj`, which is a maybe, not committed work

## Scope check

- Over-scope: none.
- Under-scope: none after review (E-06 split out; host call sites added to Scope-Paths; `question_inbox.py` removed because it is only called).

## Required tests / validation

`python3 -m pytest -o addopts="" tests/test_notify_core.py` (no `-q`, so the `N passed` line prints) and the routine gate `python3 -m pytest`.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R10.1-R10.4, R10.7, R10.8b as amended; no spec file is edited. User documentation and the CHANGELOG entry are Order 11's (`mrlblc` E-03), because the user-facing setup surface lands there.

## Open questions

### OQ-01: Use Apprise for notify-only services?

- Blocking: no
- Status: resolved
- Owner: plan author (recorded at review as decision D-1)
- Resolution or deferral rationale: RESOLVED: no. It is a large third-party dependency and the package keeps `filelock` as its only runtime dependency; spec `6kwd2e` R10.8b names a generic webhook and command hook, which reach the same services (users who want Apprise can point the command hook at its CLI).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `stat -c %a` of a file written by `save_user_config` and of a 0644 file after load, the tracked-key warning text (showing file and key, no value), and the effective-channel results for `forbid`, `bogus` and `terse-only`.
  - Observed evidence:
```
stat after save_user_config: 600
stat of 0644 file after load: 600
tightening warning text: Tightening permissions of <AW_HOME>/notify.json to 0600 (was 0o644)
tracked key warning text: Tracked file .aw/config/project.json contains forbidden secret key 'notify_webhook_url'; channel settings must live under AW_HOME or in environment variables
effective_channels for forbid: {}
effective_channels for bogus: {} [warning: Unrecognized notify_policy 'bogus' in <repo>/.aw/config/project.json; treating as 'forbid']
effective_channels for terse-only: {'webhook': {'enabled': True, 'mode': 'terse', 'url': 'https://example.com/hook'}}
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the full-mode and terse-mode outbound text for a question containing a home path, a `/srv/...` path, a `ses_` id and an ANSI escape, and a truncated field showing redaction happened before the cut.
  - Observed evidence:
```
=== FULL-MODE OUTBOUND MESSAGE ===
run run-20261017T220319Z-1894423: 1 question waiting; answer with aw runs answer run-20261017T220319Z-1894423

Question: 01-test01-a1-which-path
Error in ~<path> at <path> with session <redacted>
Options:
  1) Use ~/cfg
  2) Use <path>
aw runs answer run-20261017T220319Z-1894423 01-test01-a1-which-path

=== TERSE-MODE OUTBOUND MESSAGE ===
run run-20261017T220319Z-1894423: 1 question waiting; answer with aw runs answer run-20261017T220319Z-1894423

=== TRUNCATION AFTER REDACTION DEMONSTRATION ===
Raw input: Prefix: <home_dir>/confidential/path followed by a lot of padding characters to trigger max_text truncation
Sanitized and truncated (max_text=45): Prefix: ~<path> followed by a lot of paddi...
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `events.jsonl` lines of a scripted run showing one `notify-sent` per newly parked batch across two checkpoints, the acknowledgement after `answer-consumed`, the stale notice after `answer-stale`, a `notify-failed` event with the run's exit code unchanged, `<run_dir>/notify/sent.jsonl`, and a question file's bytes before and after (unchanged) (produced by E-03's `dispatch_checkpoint` at the top of both hosts' `run_queue`).
  - Observed evidence:
```
Question file bytes before and after (equal): True

=== events.jsonl ===
{"at": "2026-10-17T22:00:00Z", "event": "notify-sent", "channel": "command", "count": 1}
{"at": "2026-10-17T22:00:00Z", "event": "notify-sent", "channel": "command", "count": 1}
{"at": "2026-10-17T22:00:00Z", "channel": "terminal", "event": "answer-consumed", "id6": "txl556", "question_id": "09-txl556-a1-q1"}
{"at": "2026-10-17T22:00:00Z", "event": "answer-stale", "id6": "txl556", "question_id": "09-txl556-a1-q2"}
{"at": "2026-10-17T22:00:00Z", "event": "notify-failed", "channel": "command", "detail": "Command false exited with code 1"}

=== notify/sent.jsonl ===
{"channel": "command", "question_id": "09-txl556-a1-q1", "type": "question", "at": "2026-10-17T22:00:00Z", "message_id": null}
{"channel": "command", "question_id": "09-txl556-a1-q2", "type": "question", "at": "2026-10-17T22:00:00Z", "message_id": null}
{"channel": "command", "question_id": "09-txl556-a1-q1", "type": "ack", "status": "consumed", "at": "2026-10-17T22:00:00Z"}
{"channel": "command", "question_id": "09-txl556-a1-q2", "type": "ack", "status": "stale", "at": "2026-10-17T22:00:00Z"}
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the local test server's received bodies and headers for the `aw`, `text` and `ntfy` formats, the refusal for a non-loopback `http://` URL, the 302 failure event (no path or query shown), the fixture command's captured stdin, and `ls answers/` showing nothing written.
  - Observed evidence:
```
=== LOCAL SERVER RECEIVED BODIES AND HEADERS ===
Format: aw
Headers: {'Content-Type': 'application/json; charset=utf-8'}
Body: {"schema": "aw.notify/v1", "run_id": "run-v04", "mode": "terse", "count": 1, "message": "run run-v04: 1 question waiting; answer with aw runs answer run-v04", "questions": []}
Format: text
Headers: {'Content-Type': 'application/json; charset=utf-8'}
Body: {"text": "run run-v04: 1 question waiting; answer with aw runs answer run-v04"}
Format: ntfy
Headers: {'Content-Type': 'text/plain; charset=utf-8', 'Title': 'Run run-v04 questions waiting', 'Tags': 'question,warning'}
Body: run run-v04: 1 question waiting; answer with aw runs answer run-v04

=== NON-LOOPBACK HTTP REFUSAL ===
ok: False | detail: Refusing non-HTTPS URL on non-loopback host: http://evil.example.com

=== 302 FAILURE EVENT (REDACTED URL) ===
ok: False | detail: HTTP 302 from http://127.0.0.1:44371

=== FIXTURE COMMAND CAPTURED STDIN ===
ok: True
Captured stdin: {"schema": "aw.notify/v1", "run_id": "run-v04", "mode": "terse", "count": 1, "message": "run run-v04: 1 question waiting; answer with aw runs answer run-v04", "questions": []}

=== ls answers/ (NOTHING WRITTEN) ===
Contents: ''
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" tests/test_notify_core.py
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/txl556
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 24 items

tests/test_notify_core.py ........................                       [100%]

======================== 24 passed, 3 warnings in 1.62s ========================

$ aw suite
1362 passed, 3 warnings in 30.78s
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste a two-process registry round-trip (register in one subprocess, lookup in another), the `ignored` result for a duplicate event id and for an unverified sender with `ls answers/` empty, the single answer file written for a verified event (showing `channel` and `sender`), and the registry contents before and after `expire()`.
  - Observed evidence:
```
=== TWO-PROCESS REGISTRY ROUND-TRIP ===
Subprocess lookup result: {"run_dir": "<run_dir>/runs/run-v06", "question_id": "09-txl556-a1-q1", "option": 1, "artifact_hash": "", "registered_at": "2026-10-18T02:38:37.729261+00:00"}

=== UNVERIFIED SENDER ===
Outcome: ignored
ls answers/ count: 0

=== VERIFIED SENDER ===
Outcome: recorded
Answer file exists: True
Answer channel: telegram | sender: verified_user

=== DUPLICATE EVENT ID ===
Outcome: ignored

=== REGISTRY BEFORE EXPIRE ===
Routes in telegram: ['tok-xyz']
Expired count: 1

=== REGISTRY AFTER EXPIRE ===
Routes in telegram: []
```
  - Result: pass

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
