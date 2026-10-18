# IPD: Add aw notify setup, test, status and listen

- Date: 2026-10-17
- Kind: child
- Concern: Channels exist (Orders 09-10) but a human has no safe way to configure, check, or run them. Spec `6kwd2e` R10.9 requires `aw notify setup telegram` (privacy notice, hidden token input, `getMe`/`getWebhookInfo`, pairing by a one-time phrase confirmed locally, a button and reply test, save only on success) and `aw notify test` / `aw notify status`; R10.6 requires a foreground `aw notify listen` so answers for a finished run (or one whose runner holds no lock) can still be collected. Research `js5p5k` section 7 lists the hand tests needed on each OS before shipping.
- Scope: IN: the `aw notify` command family (`setup telegram|webhook|command`, `test`, `status`, `listen`, `disable <channel>`) registered in `cli.py`, each leaf declared in `command_surface.COMMAND_INVENTORY`, the bare family root answering `--agent` through `_show_family_help`, and `--agent` output on every leaf; the privacy and data notice; pairing; `deleteWebhook` only with explicit consent; a `docs/notifications.md` page covering setup, what leaves the machine, terse mode, how answers are verified, and the per-OS hand-test checklist; CHANGELOG. All config writes go through Order 09's `notify.config.save_user_config`, all Telegram traffic through Order 10's `TelegramChannel` and `TelegramReceiver`. OUT: Signal (backlog `szjsgj`); an OS service for listening (spec `6kwd2e` R10.6).
- Scope-Paths: agent_workflows/notify/cli.py, agent_workflows/notify/telegram.py, agent_workflows/notify/config.py, agent_workflows/cli.py, agent_workflows/command_surface.py, tests/test_notify_cli.py, docs/notifications.md, docs/README.md, CHANGELOG.md
- Scope-Exceeded: agent_workflows/term.py (Add is_interactive method on Term class)
- Item-Dependencies: executed:qrup8m
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Spec: 6kwd2e
- Set: qchan
- Order: 11
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: mrlblc

## Workflow history
- 2026-10-18 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: mrlblc verified (set qchan, attempt 1). [Scope reconciliation - out-of-scope agent_workflows/term.py: Add is_interactive method on Term class; in-scope-unmodified agent_workflows/notify/config.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008
- 2026-10-17 to-review (aw set): authored review-ready against spec 6kwd2e (amended 2026-10-17)

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Give the maintainer a guided, verifiable way to turn on phone notifications and answers, and to check and run them (spec `6kwd2e` R10.9, R10.6).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: setup

- [x] E-01 Add `aw notify setup telegram` in `notify/cli.py`. It refuses to start (exit 2, nothing written) unless `term.is_interactive()` is true, because every step needs a human; `--agent` with setup is a usage error for the same reason. Steps: (1) print what leaves the machine (in terse mode only the run id, the question count and the answer command; in full mode the sanitized question text and options), that Telegram can read bot chats (they are not end-to-end encrypted), and that terse is the default; (2) read the token with `getpass.getpass` (never an argument, so it never enters shell history or `ps`), or from `AW_NOTIFY_TELEGRAM_TOKEN` when set; (3) call `getMe` and refuse on 401 with a clear message; (4) call `getWebhookInfo` and, if a webhook is set, explain that polling cannot run beside it and call `deleteWebhook` only on an explicit `y`; a refusal exits 1 writing nothing; (5) take Order 10's per-bot receiver lock (`<AW_HOME>/notify/telegram-<bot_id>.lock`, non-blocking) so setup never races a live runner's poll (a 409); if a runner holds it, exit 1 with "stop the run or use a second bot"; (6) generate a one-time phrase with `secrets.token_urlsafe(8)`, print it and the `https://t.me/<bot_username>?start=<phrase>` link, and long-poll for at most 5 minutes for a PRIVATE message whose text contains it, ignoring every other update; (7) show the sender's name, numeric user id and chat id and require a `y`; (8) send a test question with two buttons and `force_reply` and require one button press and one threaded reply FROM THE PAIRED IDS, acknowledging both; (9) only then write the channel with `notify.config.save_user_config` (0600; `mode: terse`, or `full` with `--full`), and print `aw notify test` and `aw notify status`. Ctrl-C, a timeout or a declined confirmation at any step exits 1 writing nothing, and setup advances the update offset past everything it consumed so a later runner does not re-read the pairing traffic.
  - Depends on: none
  - Expected outcome: against the fake Bot API with scripted stdin, setup pairs, runs both tests and writes the config with mode 0600 and `mode: terse`; a wrong token exits nonzero and writes nothing; declining the identity confirmation, declining `deleteWebhook`, a pairing timeout, and a held receiver lock each write nothing; a message from another user containing the phrase is not accepted as pairing; with stdin not a TTY setup exits 2 (A54).
  - Execution state: performed

- [x] E-05 Add `aw notify setup webhook --url URL [--format aw|text|ntfy] [--full]` and `aw notify setup command [--full] -- <argv...>`: send one test notification through Order 09's `webhook` / `command` channel (`txl556` E-04), and only on success save it with `save_user_config` (terse unless `--full`). The URL is a secret: it is accepted on the command line only with a printed warning that it lands in shell history, and is preferred from `--url-stdin` (read with `getpass`) or `AW_NOTIFY_WEBHOOK_URL`; output and errors show only its scheme and host. These two need no TTY, so they work in scripts.
  - Depends on: E-01
  - Expected outcome: against a loopback webhook server each format's test notification arrives and the channel is saved; a server returning 500 saves nothing and exits 1; `--url-stdin` reads the URL without echo; no output line contains the URL path.
  - Execution state: performed

### Task group 2: operate

- [x] E-02 Add `aw notify status`, `aw notify disable <channel>` and `aw notify test [<channel>]`. `status` (read-only): per configured channel its source (user config or env), `enabled`, `mode`, the tracked `notify_policy` ceiling in force (Order 09 `read_notify_policy`), the receiver lock holder pid or `none` (read from the lock's sidecar, never by taking it), and the last `notify-sent` / `notify-failed` it can find, never printing a token, chat id or webhook path; with no channel configured it prints how to set one up and exits 0. `disable <channel>` sets `enabled: false` through `save_user_config` (exit 1 for an unknown channel); an env-configured channel cannot be disabled this way and the command says to unset the variable. `test [<channel>]` sends a terse test notification to each (or the named) effective channel and, for Telegram, waits up to 2 minutes for one button press, which requires the receiver lock as E-01 step 5 does; exit 0 all delivered, 1 any failed. Every leaf supports `--agent` (one `aw.agent/v1` result record through `agent_schema`, `exit` equal to the process exit code) and `--json`.
  - Depends on: E-05
  - Expected outcome: `status --agent` validates with `agent_schema.validate_agent_record` and its output contains no token or chat id; after `disable telegram` a `dispatch_checkpoint` sends no request to the fake server; `test` with a failing webhook exits 1.
  - Execution state: performed

- [x] E-06 Add `aw notify listen`: in the foreground, call Order 10's `ensure_receiver` path without a run (a `TelegramReceiver` holding the per-bot lock, routing every inbound event through Order 09's `core.apply_inbound` for every run directory in the registry), print one line per recorded or rejected answer, and stop cleanly on Ctrl-C or SIGTERM, releasing the lock (exit 0). If another process holds the lock, exit 1 naming its pid. With no Telegram channel configured, exit 1 with the setup hint. Its events go to `<AW_HOME>/notify/listen.jsonl`, since there is no run directory.
  - Depends on: E-02
  - Expected outcome: with a finished run holding an open question registered in the registry, a button press sent to the fake server while `listen` runs writes that question's answer file with `channel: telegram`; a second `listen` exits 1 naming the first's pid; SIGTERM ends the first with exit 0 and the lock released.
  - Execution state: performed

- [x] E-03 Register the family and document it. In `cli.py`: add the `notify` subparser with its leaves, a `_DESCRIPTIONS["notify"]` entry, and a bare `aw notify` that calls `_show_family_help(parser, "notify", "aw notify status", term, context)` so `aw notify --agent` emits the conforming `cannot-run` record the family-root conformance test requires. In `command_surface.COMMAND_INVENTORY`, declare each leaf: `notify status` `command_class="read"`, exit `(0, 2)`; `notify setup telegram`, `notify setup webhook`, `notify setup command`, `notify disable` `command_class="mutation"`, exit `(0, 1, 2)`; `notify test` and `notify listen` `command_class="mutation"` (both send messages off the machine; `listen` writes answer files), exit `(0, 1, 2)`. The inventory has exactly four non-alias classes (`bare`, `check`, `mutation`, `read`; measured at review), so a network-sending verb is a `mutation` (D-3). Write `docs/notifications.md` (user-facing prose, no em or en dashes) and link it from `docs/README.md`: setup for Telegram, webhook (ntfy, Teams Workflows, Google Chat, using the `text` and `ntfy` formats) and command hook; what leaves the machine; terse versus full; how answers are verified (paired numeric ids, private chat, replies only to a known question message); one bot per machine and why; `aw runs answer` as the always-available fallback; `aw notify listen` for answering a finished run; and the hand-test checklist per OS from research `js5p5k` section 7 (proxy, macOS certificates, sleep and wake, two runners, two machines, spoofing, double answers, long and non-BMP text, no token in logs, Teams Workflow rendering of the `text` body). Add a `CHANGELOG.md` entry (no em or en dashes).
  - Depends on: E-06
  - Expected outcome: `tests/test_command_surface_declarations.py`, `tests/test_conformance_matrix_structure.py` and `tests/test_family_root_agent_conformance.py` pass with the new family; every command line in the doc parses under the implemented `--help`; `aw sanitize --agent` is clean.
  - Execution state: performed

### Task group 3: tests

- [x] E-04 Add `tests/test_notify_cli.py` (marked `pytest.mark.core`) driving every leaf as a subprocess (`sys.executable -m agent_workflows notify ...`) under the conftest `AW_HOME` sandbox, against Order 10's `tests/fake_telegram.py` (pointed at with `AW_NOTIFY_TELEGRAM_BASE_URL`) and a loopback webhook server. Setup is driven through a pseudo-terminal (`pty`, skipped with a stated reason where unavailable) with scripted input, including the hidden-token prompt; the doc check parses each `aw notify ...` command line found in `docs/notifications.md` with the real parser (`cli._build_parser().parse_args`), which tests the doc against the CLI rather than reading production source.
  - Depends on: E-03
  - Expected outcome: the module passes; no test contacts a host other than loopback; the routine gate passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- New verbs register in `cli.py` and are declared one per leaf in `command_surface.COMMAND_INVENTORY`; `tests/test_command_surface_declarations.py` fails on an undeclared leaf, and `tests/test_family_root_agent_conformance.py` runs `aw <root> --agent` for every family root (23 today) and requires a valid `aw.agent/v1` record, which `cli._show_family_help` provides for a bare family.
- User-facing docs and CHANGELOG avoid em and en dashes (AGENTS.md).
- Secrets are read with hidden input (`getpass`) and never printed or logged; channel config is written only through Order 09's `notify.config.save_user_config`.
- Presence for a CLI prompt is `term.is_interactive()` (the `aw` CLI's own predicate); the runner predicate `is_interactive_run` is for runner gates.
- Tests run under the conftest `AW_HOME` sandbox.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Research `kdg4uz` and `js5p5k` both recommend pairing by a one-time phrase rather than an 'id bot', and a button-plus-reply round trip before saving.
- Telegram allows one `getUpdates` consumer per bot; setup, `test` and `listen` all poll, so each must take Order 10's per-bot lock or it will 409 a live runner's receiver (research `kdg4uz`: "Serialize setup polling through the same broker").
- A webhook URL and a bot token are both bearer credentials; command-line arguments are visible in shell history and process listings.

## Proposed changes (ordered, validatable)

1. E-01 Telegram setup. 2. E-05 webhook and command setup. 3. E-02 status, disable, test. 4. E-06 listen. 5. E-03 registration, declarations, docs, CHANGELOG. 6. E-04 tests.

## Deferred / out of scope (with reason)

- Signal: backlog `szjsgj` (parked).
  - Carrier-Declined: not shipped by decision (spec `6kwd2e` R10.10); a possible later channel is recorded as parked backlog `szjsgj`, which is a maybe, not committed work
- Installing a background OS service for listening: excluded by spec `6kwd2e` R10.6.
  - Carrier-Declined: excluded by spec `6kwd2e` as a design decision, not deferred work
- Storing the token in the OS keyring: research `kdg4uz` prefers it; spec `6kwd2e` R10.2 requires only a 0600 user file or an environment variable, and a keyring backend is a new dependency.
  - Carrier-Declined: not required by spec `6kwd2e` R10.2 and would add a runtime dependency beyond `filelock`

## Scope check

- Over-scope: none.
- Under-scope: none after review (E-05 and E-06 split out; `docs/README.md` added to Scope-Paths).

## Required tests / validation

`python3 -m pytest -o addopts="" tests/test_notify_cli.py tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_family_root_agent_conformance.py` (no `-q`, so the `N passed` line prints) and the routine gate `python3 -m pytest`.

## Spec / documentation sync

Implements spec `6kwd2e` R10.9 and the R10.6 `aw notify listen` companion as amended; no spec file is edited. User documentation is `docs/notifications.md` (linked from `docs/README.md`) and the CHANGELOG entry, both owned here for the whole channel layer (Orders 09 and 10 point here).

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the scripted setup transcript against the fake API (notice, pairing, both tests), the saved config's `stat -c %a` and its `mode: terse`, and for the wrong-token, declined-identity, declined-webhook-deletion, pairing-timeout, held-lock and non-TTY runs the exit code plus `ls <AW_HOME>/notify.json` showing no file; and the fake server log showing the other user's phrase message not accepted.
  - Observed evidence:
    1. Scripted setup transcript against fake Bot API:
       ```
       Privacy & Data Notice for Telegram Notifications:
         - In terse mode (default), notifications contain only the run id, question count, and answer command.
         - In full mode, notifications contain sanitized question text and option choices.
         - Telegram bot chats are not end-to-end encrypted: Telegram servers can process bot messages.
         - Terse mode is the default.

       Enter Telegram bot token:
       Verified bot: @fake_bot (ID: 123456789)

       Please send the following phrase to your bot:
         x5a8mmtg49o
       Or open this link: https://t.me/fake_bot?start=x5a8mmtg49o

       Waiting for pairing message (up to 5 minutes)...

       Detected pairing request:
         Name: TestUser
         User ID: 424242
         Chat ID: 424242
       Confirm identity and pair? [y/N]: y

       Sending test question with buttons and reply prompt...
         Button click confirmed.
         Threaded reply confirmed.

       Setup complete! Telegram notifications configured.
       Saved to notify.json (mode: terse).

       Run checks:
         aw notify test
         aw notify status
       ```
    2. Config permissions and content:
       `stat -c %a notify.json`: `600`
       `notify.json`:
       ```json
       {
         "telegram": {
           "enabled": true,
           "token": "123456789:ABCfakeTokenXYZ",
           "chat_id": "424242",
           "user_id": "424242",
           "mode": "terse"
         }
       }
       ```
    3. Error case exit codes and `notify.json` absence:
       - Wrong token: exit 1, `ls notify.json`: No such file or directory
       - Declined identity: exit 1, `ls notify.json`: No such file or directory
       - Declined webhook deletion: exit 1, `ls notify.json`: No such file or directory
       - Pairing timeout / aborted: exit 1, `ls notify.json`: No such file or directory
       - Held lock: exit 1 ("stop the run or use a second bot"), `ls notify.json`: No such file or directory
       - Non-TTY execution: exit 2 ("requires an interactive terminal"), `ls notify.json`: No such file or directory
    4. Group message update from user 88888 with pairing phrase:
       Fake server log shows no pairing request detected from 88888, only private message from 424242 accepted.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `aw notify status --agent` output (with a check that it contains neither the token nor the chat id), the fake server request log after `disable telegram` and a `dispatch_checkpoint` (no `sendMessage`), and the exit code of `test` against a failing webhook.
  - Observed evidence:
    1. `aw notify status --agent` output:
       ```json
       {"schema":"aw.agent/v1","kind":"result","cmd":"notify status","outcome":"ok","exit":0,"verified":true,"complete":true,"findings":0,"next":null}
       ```
       Sanitization check confirmed: output contains neither the token ("secret_bot_token_999": False) nor chat id ("999888777": False) nor webhook path ("/secret/webhook/path": False).
    2. Disable telegram and delivery check:
       `aw notify disable telegram` exited 0.
       Subsequent notification test dispatched 0 `sendMessage` calls to fake Telegram server (fake.requests for sendMessage: `[]`).
    3. `aw notify test webhook` against failing HTTP 500 endpoint:
       Exit code: 1
       Stderr: `Webhook test failed: HTTP 500 from http://127.0.0.1:39145`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the runner output of the three CLI conformance tests with the new family, `aw notify --agent` output, the list of `aw notify ...` lines from `docs/notifications.md` with each parse result, and the `aw sanitize --agent` result.
  - Observed evidence:
    1. CLI conformance tests runner output:
       ```
       tests/test_command_surface_declarations.py ..                            [ 33%]
       tests/test_conformance_matrix_structure.py ........                      [ 48%]
       tests/test_family_root_agent_conformance.py .....s...................... [ 98%]
       ================== 38 passed, 1 skipped in 13.78s ==================
       ```
    2. `aw notify --agent` root output:
       ```json
       {"schema":"aw.agent/v1","kind":"error","cmd":"notify","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"target":"notify","findings":0,"next":"aw notify status"}
       ```
       Exit code: 2
    3. `docs/notifications.md` command lines parsed with `cli._build_parser()`:
       - `aw notify disable command`: PASS
       - `aw notify disable telegram`: PASS
       - `aw notify disable webhook`: PASS
       - `aw notify listen`: PASS
       - `aw notify setup command -- /usr/local/bin/my-alert-script --channel ops`: PASS
       - `aw notify setup telegram`: PASS
       - `aw notify setup telegram --full`: PASS
       - `aw notify setup webhook --url-stdin --format aw`: PASS
       - `aw notify status`: PASS
       - `aw notify test`: PASS
       - `aw notify test command`: PASS
       - `aw notify test telegram`: PASS
       - `aw notify test webhook`: PASS
    4. `aw sanitize --agent` result:
       ```json
       {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5942,"findings":0,"evidence":["leak-scan"],"next":null}
       ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the runner output of the test command and the routine gate, including `N passed`.
  - Observed evidence:
    1. Required test command:
       `python3 -m pytest -o addopts="" tests/test_notify_cli.py tests/test_command_surface_declarations.py tests/test_conformance_matrix_structure.py tests/test_family_root_agent_conformance.py`:
       ```
       ================== 55 passed, 1 skipped, 5 warnings in 45.26s ==================
       ```
    2. Routine gate (`aw suite`):
       ```
       1660 passed, 11 warnings in 75.23s (0:01:15)
       ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the loopback server's received body for each format, the saved channel entries, the 500 case's exit code with no channel saved, and every output line of the runs showing no URL path.
  - Observed evidence:
    1. Loopback server received bodies:
       - `aw` format: `{"schema": "aw.notify/v1", "run_id": "setup-test", "mode": "terse", "count": 0, "message": "aw notify setup test notification", "questions": []}`
       - `text` format: `{"text": "aw notify setup test notification"}`
       - `ntfy` format: `aw notify setup test notification` (Headers: `Title: Run setup-test questions waiting`, `Tags: question,warning`)
    2. Saved webhook channel entry in `notify.json`:
       ```json
       {
         "webhook": {
           "enabled": true,
           "url": "http://127.0.0.1:36279/secret/path/ntfy",
           "format": "ntfy",
           "mode": "terse"
         }
       }
       ```
    3. 500 case:
       Exit code: 1
       `notify.json exists`: False
       Stderr:
       ```
       WARNING: Webhook URL passed on the command line may be recorded in shell history.
       Webhook test failed: HTTP 500 from http://127.0.0.1:45047
       ```
    4. Path redaction across all runs:
       Output lines show only scheme and host: `Webhook configured successfully for http://127.0.0.1:36279 (format=aw, mode=terse).`
       Secret path `/secret/path/...` never appears in stdout or stderr.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `listen` output line and the answer file written for the finished run's question, the second `listen`'s exit code and message, and the first `listen`'s exit code after SIGTERM with the lock file free (produced by E-06's foreground receiver).
  - Observed evidence:
    1. `listen` output line:
       ```
       aw notify listen running in foreground. Press Ctrl-C to stop.
       Answer recorded: recorded from sender 424242
       ```
    2. Answer file written (`answers/01-it0001-a1-q1.json`):
       ```json
       {
         "schema": "aw.answer/v1",
         "question_id": "01-it0001-a1-q1",
         "answer": "Prod",
         "choice": 1,
         "actor": "human",
         "channel": "telegram",
         "sender": "424242",
         "artifact_hash": "e6da846241176f047909f4a3d3112e84a8a15b9bfc070a3b84118ff2bfaca5d8",
         "applied_to": [
           {
             "question_id": "01-it0001-a1-q1",
             "artifact_id6": "it0001"
           }
         ],
         "answered_at": "2026-10-18T04:44:10.780267+00:00"
       }
       ```
    3. Second `listen` invocation while lock is held:
       Exit code: 1
       Stderr: `Error: Telegram receiver lock held by pid 1656753.`
    4. First `listen` termination:
       Process signaled with SIGTERM.
       Exit code: 0
       Receiver lock released; lock acquired immediately by subsequent test.
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
