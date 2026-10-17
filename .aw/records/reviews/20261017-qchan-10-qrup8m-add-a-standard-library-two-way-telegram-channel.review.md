# Review findings: plan qrup8m

- Subject-Id: qrup8m
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan. Prerequisite `txl556` is `reviewed` (revised in this sweep); its contract was read from the revised plan.

Verified:
- `txl556` (as revised) E-02 `Channel` protocol and `build_batch`/`sanitize_outbound`; E-06 `notify/registry.py` and `core.apply_inbound` (dedup, `verify`, routing, `question_inbox.write_answer`, "Order 10 calls this rather than mapping events itself"); E-03 `dispatch_checkpoint` at the top of both hosts' `run_queue`, sending acknowledgements for `answer-consumed`/`answer-stale` once.
- `runner_shared.register_active_sampler` / `stop_active_samplers`, called by `runner_shutdown.clean_shutdown`, are the existing mechanism for stopping daemon threads on shutdown.
- MEASURED: for a 401 from a local server at `.../bot<token>/getMe`, `urllib.error.HTTPError` has `str(e) == "HTTP Error 401: Unauthorized"` but `e.filename` and `e.geturl()` both hold the full token-bearing URL.
- `pyproject.toml`: `requires-python = ">=3.9"`, `dependencies = ["filelock>=3"]`; installed `filelock` 4.0.9.
- Research `kdg4uz`: callback data 1-64 bytes; 100 updates per batch; 24 h retention; 409 for a competing poll; a file lock does not coordinate machines; `sendMessage` has no client request id; 25 s poll and 40 s timeout; plain text; disable previews; require private chat type as well as ids.
- Spec `6kwd2e` R10.1, R10.4, R10.5, R10.6, R10.8a, A50, A51, A52 read as cited.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Architecture (single inbound path, R10.1) | old E-02 "becomes `write_answer(choice=<index>)`"; old E-04 "Order 09 `on_consumed`"; `txl556` E-06, E-03 | The adapter mapped events to the answer writer itself and called an `on_consumed` hook that the revised Order 09 does not define. That duplicates the core's verification, dedup and routing, and R10.1 assigns those to the core. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-02 translates updates into `InboundEvent`s for `core.apply_inbound`; new E-06 implements acknowledgements as the channel side of `dispatch_checkpoint`. Scope-Paths drop `registry.py` and `runner_shared.py`. |
| PR-002 | HIGH | IN-SCOPE | Security (token leakage) | measured: `HTTPError.filename`/`geturl()` carry the token URL | "Every exception message has the token redacted" misses the exception object itself: the URL sits in attributes and in a chained traceback, which a `notify-failed` event or a crash report would expose. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | E-01: one `_call` catches every transport error and raises `TelegramError ... from None` with no URL, plus a final token replace; V-01 demands `str`, `repr` and formatted traceback without the token. |
| PR-003 | HIGH | UNDER-SCOPE | Correctness (receiver lifecycle) | old E-03 "daemon thread at run start ... until the run ends" | Start site, stop path and lock release were unspecified: no shutdown hook, no bound on the join of a 25 s long poll, no behavior on `resume`, and the receiver's event destination was undefined. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03: `ensure_receiver` at the top of both hosts' `run_queue` (start and resume) and at each checkpoint for takeover; registered with `register_active_sampler`; explicit stop before the summary with a 45 s bound; events to the starting run's `events.jsonl`. |
| PR-004 | MEDIUM | IN-SCOPE | Correctness (terse mode, R10.4) | spec R10.4 "no question content and no buttons"; old E-01 always buttons | Sends always carried inline keyboards and `force_reply`, which terse mode forbids and terse is the default. | all Low | FIXED | E-01: terse sends one message per batch with no `reply_markup`; full sends per-question keyboards. |
| PR-005 | MEDIUM | IN-SCOPE | Correctness (verify, offset, replay) | research `kdg4uz` "`chat.get('type') == 'private'`"; "Process each update ... then persist `update_id + 1`" | Verification did not check `chat.type`; on a failed write the plan said "do not advance" but not what happens to the rest of the batch, and a replay was not covered. | all Low | FIXED | E-01 VERIFY checks `chat.type == "private"` (callbacks via their message's chat); E-02 stops the batch, persists the last handled offset, backs off, and relies on first-answer-wins for replays; V-02 covers bot sender and replay. |
| PR-006 | MEDIUM | IN-SCOPE | Correctness (uncertain send, limits) | research `kdg4uz` "A send timeout may mean the message was sent"; "4096 characters after entity parsing" | Send-timeout behavior was unspecified (blind retry duplicates), and the 4096 limit had no margin or surrogate-safe truncation rule. | all Low | FIXED | E-01: `notify-uncertain` event and no automatic resend; 4000 UTF-16-unit budget truncated without splitting a surrogate pair. |
| PR-007 | MEDIUM | UNDER-SCOPE | Testing / safety | old E-05 "a base-URL setting used only by tests"; core-tier rule; multi-machine 409 | The test base-URL override could point real tokens at an arbitrary host; long-poll threads would make tests slow; multi-machine sharing was not stated as a limit. | all Low | FIXED | Override restricted to `https` or loopback `http`; test-only short poll timeouts; module marked core; Deferred declines a cross-machine broker with reason. |
| PR-008 | LOW | IN-SCOPE | Process | OQ-01 `Owner: maintainer`; `-q` | OQ-01 was settled by the spec, not by a maintainer answer; `-q` hides `N passed`. | all Low | FIXED | Owner corrected (D-1); `-q` removed. |

`aw ipd lint --phase review-finalize --agent`: `clean` (one `info` advisory `IPD-Z602` on E-01's clause count, kept per D-3).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Plain text or HTML? (OQ-01) | Plain text, no `parse_mode`. | HTML/MarkdownV2 (REJECTED: escaping failures drop messages; spec requires plain text). | spec R10.8a; research `kdg4uz`. | yes |
| D-2 | Resend after a send timeout? | No; record `notify-uncertain`. | Automatic resend (REJECTED: duplicates, no client request id). | research `kdg4uz`. | yes |
| D-3 | Split E-01 (transport, send, receive, verify, ack, health)? | Keep as one item. | Split per method (REJECTED: one class over one transport, verified by one fake server; the parts are not independently useful). | rubric G right-sizing (a)-(d) judged no; `IPD-Z602` is advisory. | yes |
| D-4 | Who sends the "answered" acknowledgement? | Order 09's `dispatch_checkpoint` via this channel's `send` (E-06). | A new `on_consumed` hook (REJECTED: not defined by revised `txl556`; a second notification path). | `txl556` E-03. | yes |
| D-5 | Cross-machine coordination? | Out of scope; 409 stop plus one-bot-per-machine. | Remote broker (REJECTED: new product scope). | research `kdg4uz`; spec R10.6 "per machine". | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
