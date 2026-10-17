# IPD: Add aw notify setup, test, status and listen

- Date: 2026-10-17
- Kind: child
- Concern: Channels exist (Orders 09-10) but a human has no safe way to configure, check, or run them. Spec `6kwd2e` R10.9 requires `aw notify setup telegram` (privacy notice, hidden token input, `getMe`/`getWebhookInfo`, pairing by a one-time phrase confirmed locally, a button and reply test, save only on success) and `aw notify test` / `aw notify status`; R10.6 requires a foreground `aw notify listen` so answers for a finished run (or one whose runner holds no lock) can still be collected. Research `js5p5k` section 7 lists the hand tests needed on each OS before shipping.
- Scope: IN: the `aw notify` command family (`setup telegram|webhook|command`, `test`, `status`, `listen`, `disable <channel>`) with exit contracts and `--agent` output; the privacy and data notice; pairing; `deleteWebhook` only with explicit consent; a `docs/` page covering setup, what leaves the machine, terse mode, and the per-OS hand-test checklist; CHANGELOG. OUT: Signal (backlog `szjsgj`).
- Scope-Paths: agent_workflows/notify/cli.py, agent_workflows/notify/telegram.py, agent_workflows/notify/config.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_notify_cli.py, docs/notifications.md, CHANGELOG.md
- Item-Dependencies: executed:qrup8m
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 11
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: mrlblc

## Workflow history
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give the maintainer a guided, verifiable way to turn on phone notifications and answers, and to check and run them (spec `6kwd2e` R10.9, R10.6).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: setup

- [ ] E-01 Add `aw notify setup telegram`: print what leaves the machine and that Telegram can read bot chats (they are not end-to-end encrypted), and that terse mode is the default; read the bot token with `getpass`; call `getMe` (refuse on 401 with a clear message) and `getWebhookInfo` (if a webhook is set, ask before calling `deleteWebhook`); print a one-time random phrase and long-poll until a private message containing it arrives (5 minute bound), then show the sender's name, user id and chat id and ask the human to confirm; send a test question with two buttons and `force_reply`, and require one button press and one threaded reply; only then write the config (0600) with `mode: terse`. `--full` opts into content. Also `aw notify setup webhook --url` and `setup command -- <argv>` (send a test notification, save on success).
  - Depends on: none
  - Expected outcome: against the fake Bot API the setup pairs, runs both tests and writes the config; a wrong token exits nonzero and writes nothing; declining the confirmation writes nothing (A54).
  - Execution state: pending

### Task group 2: operate

- [ ] E-02 Add `aw notify test [<channel>]` (send a test notification and, for two-way channels, wait for one button press), `aw notify status` (per channel: enabled, mode, last success, receiver holder pid or none, last error, without printing secrets), `aw notify disable <channel>`, and `aw notify listen` (take the receiver lock in the foreground and route answers for every run directory in the registry until Ctrl-C), each with exit codes in `command_surface` and `--agent` output.
  - Depends on: E-01
  - Expected outcome: `status` lists the fake channel without its token; `listen` writes an answer for a finished run's open question; `disable` stops further sends.
  - Execution state: pending

### Task group 3: docs and tests

- [ ] E-03 Write `docs/notifications.md` (user-facing prose, no em or en dashes): setup for Telegram, webhook (ntfy, Teams Workflows, Google Chat examples) and command hook; what leaves the machine; terse versus full; how answers are verified; `aw runs answer` as the always-available fallback; and the hand-test checklist per OS from research `js5p5k` section 7 (proxy, macOS certificates, sleep and wake, two runners, two machines, spoofing, double answers, long and non-BMP text, no token in logs). Add a CHANGELOG entry.
  - Depends on: E-02
  - Expected outcome: the doc exists and its commands match the implemented `--help` output; `aw sanitize --agent` is clean.
  - Execution state: pending

- [ ] E-04 Add `tests/test_notify_cli.py` driving the commands as subprocesses against `tests/fake_telegram.py` (from Order 10) and a local webhook server, with stdin scripted for the confirmations.
  - Depends on: E-03
  - Expected outcome: the module passes; no test touches a real service.
  - Execution state: pending

## Project conventions discovered (Step 0)

- New verbs register in `cli.py` and declare exit contracts in `command_surface`.
- User-facing docs and CHANGELOG avoid em and en dashes (AGENTS.md).
- Secrets are read with hidden input and never printed or logged.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Research `kdg4uz` and `js5p5k` both recommend pairing by a one-time phrase rather than an 'id bot', and a button-plus-reply round trip before saving.

## Proposed changes (ordered, validatable)

1. E-01 setup. 2. E-02 test/status/disable/listen. 3. E-03 docs + changelog. 4. E-04 tests.

## Deferred / out of scope (with reason)

- Signal: backlog `szjsgj` (parked).
  - Carrier-Declined: not shipped by decision (spec `6kwd2e` R10.10); a possible later channel is recorded as parked backlog `szjsgj`, which is a maybe, not committed work
- Installing a background OS service for listening: excluded by spec `6kwd2e` R10.6.
  - Carrier-Declined: excluded by spec `6kwd2e` as a design decision, not deferred work

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest -o addopts="" -q tests/test_notify_cli.py` and the routine gate.

## Spec / documentation sync

N/A: implements spec `6kwd2e` R10.9 and the R10.6 `aw notify listen` companion as amended.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the scripted setup transcript against the fake API (pairing, both tests, saved config with `mode: terse` and file mode 0600), and the wrong-token and declined runs showing no config written.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw notify status` output (no token visible), the `listen` run writing an answer for a finished run's question, and a send attempt after `disable` producing no request at the fake server.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the doc's command lines next to the matching `--help` excerpts, and the `aw sanitize --agent` result.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
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
