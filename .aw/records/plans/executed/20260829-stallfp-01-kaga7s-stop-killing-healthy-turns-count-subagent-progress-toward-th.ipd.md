# IPD: Stop killing progressing turns: count subagent progress toward the stall watchdog and make the heartbeat show the stall countdown

- Date: 2026-08-29
- Kind: child
- Concern: The driver KILLS TURNS THAT ARE STILL PROGRESSING. `StallWatchdog` (oc_runipd.py:132-167) and `Heartbeat` are advanced ONLY by lines arriving on the child's stdout (`heartbeat.touch()`/`watchdog.touch()`, oc_runipd.py:1775-1776). The `opencode run --format json` stdout stream carries ONLY parent-session events (`step_start`/`step_finish`/`text`/`tool_use`, tallied across recent `sessions/*.jsonl`), so any work the parent turn performs WITHOUT producing a parent-session event is invisible to the stall decision, and at DEFAULT_STALL_TIMEOUT (600.0s, oc_runipd.py:1629) the driver terminates it. Subagent (Task) delegation is one such blind spot and is REPRODUCED here (see Findings: a live `opencode run` reproduction shows a 24.6s parent-stdout gap spanning an entire subagent session, with the child's progress visible only in opencode's own log). The stdout-only signal is the defect; the exact blind spot in any one incident is secondary. Cost: silently discarded long turns - 4 `ipd-stalled` kills recorded on 2026-08-29 alone (`.aw/records/runs/*/events.jsonl`). SEPARATELY, genuine hangs DO exist (backlog `qyaime`: a worktree-isolated `--auto` turn blocks forever on an unanswerable `external_directory` permission prompt), so the timeout cannot simply be raised - the fix must DISTINGUISH real progress from a real hang. Compounding the confusion, the heartbeat prints `still working on X (Nm elapsed, Nm since last event)`, which reads as reassurance while a kill countdown is silently running.
- Scope: Make the stall decision progress-aware and the display honest, for the OPENCODE driver only. (1) Add a best-effort progress observer that tails opencode's own log (`$XDG_DATA_HOME`/`~/.local/share/opencode/log/opencode.log`) and reports progress for activity attributable to the current turn's process, then `touch()`es the watchdog/heartbeat from it, so a turn whose work is inside a Task is not treated as idle. The attribution key is the log's per-CLI-process `run=<id>` token, NOT `parentID` (see Findings PR-001: `parentID` appears ONLY on the one-shot `message=created` line, never on ongoing child lines; a child-session line carries `session.id=<child>` with no parent reference, so `parentID` matching cannot observe ongoing progress). Because the driver does not currently know its child's `run=` id, E-01 must FIRST establish a sound attribution mechanism from evidence and record it; if no sound in-process attribution exists, that is a REPLAN trigger, not something to approximate. Treat the log as an OPTIONAL, best-effort signal: if it cannot be read/parsed, behavior degrades to today's stdout-only watchdog (never a hard dependency, never a crash). (2) Make the heartbeat state the countdown instead of implying health: report time since last observed progress AND the remaining time before the stall kill (e.g. `no progress 7m30s; stall kill in 2m30s`), and name WHICH source last showed progress (stdout vs subagent). (3) Preserve the true-hang guarantee: an unanswerable permission prompt still produces no progress from EITHER source and must still be killed at the timeout. NOTE the agy driver is deliberately EXCLUDED (see Deferred): `agy --output-format stream-json` ALREADY emits `step_type == "subagent"` events on stdout (agy_runipd.py:234-243), which already touch the watchdog, so agy does not have this bug and needs no observer. The shared display change lands in `render_stream.Heartbeat`; agy carries its own duplicate `Heartbeat` copy (agy_runipd.py:247-296), so the display fix must either be applied to both or agy must be switched to the shared class.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, agent_workflows/stall_progress.py, tests/
- Item-Dependencies: none
- Status: executed
- Set: stallfp
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: kaga7s

## Workflow history
- 2026-08-30 executed (opencode its_direct/pt3-claude-opus-5-1m-us): subagent progress now counts toward the stall watchdog; honest kill countdown sourced from the watchdog
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; Readiness: GO - PENDING HUMAN APPROVAL. PR-001..PR-012 all FIXED in place. Core attribution key (parentID on ongoing child lines) DISPROVEN and replaced with the two-hop parent-session route; the cited w0ln4q incident corrected (last stdout event is a completed bash call, no task tool_use, and the log shows >3min total silence before the kill, so the observer would not have saved it); the agy observer removed as unfounded (agy already emits subagent events on stdout); added the noisy-hang true-positive guarantee, a watchdog-sourced countdown, duplicate-Heartbeat unification, leak-safe fixtures, and offset/thread bounds. OQ-02 raised and resolved from live evidence.
- 2026-08-29 to-review (aw set): Authored review-ready: subagent progress must count toward the stall watchdog; heartbeat must show the kill countdown. Evidence-backed by run-20260829T142239Z (healthy turn killed) and jolfpj (true hang preserved).

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Stop the opencode driver from terminating turns that are genuinely progressing inside a subagent, by feeding attributable subagent activity into the stall watchdog, while KEEPING the real-hang kill intact (including the realistic noisy hang, where a permission-deadlocked process still emits background log lines) and making the heartbeat state the actual countdown, sourced from the watchdog itself, instead of implying everything is fine. Success is BOTH halves: a progressing turn survives AND a deadlocked turn still dies. A change that only stops the kills would be a regression, because an immortal run is less recoverable than a killed one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: observe subagent progress

- [x] E-01 CONFIRM the attribution mechanism against the running opencode before writing the observer, and record the confirmation. The mechanism is already DECIDED (OQ-02): two-hop parent-session attribution (read our parent session id from the first stdout event; match `message=created ... parentID=<our parent id>` to learn each child session id; count that child's `session.id=<child>` lines), counting ONLY `message=loop`/`message=process`/`message=stream` as progress and excluding all housekeeping (`evaluated`, `asking`, `llm runtime selected`, `tracking`, `resolved path`, `touching file`). Do NOT re-litigate the design; VERIFY it still holds on the installed version, and capture the redacted log excerpt that becomes the E-02 fixture. If the format has changed such that the route no longer works, STOP and report a REPLAN rather than shipping an approximation.
  - Depends on: none
  - Expected outcome: a recorded, evidence-cited confirmation that the two-hop route and the progress/noise classification hold on the installed opencode version, plus the redacted fixture excerpt. No production code is required by this item.
  - Execution state: performed

- [x] E-02 Build the shared progress observer module using the E-01 mechanism: tail opencode's log and report "progress at time T" only for lines attributable to the current turn AND classified as agent-loop progress. Resolve the log path from `XDG_DATA_HOME` with the `~/.local/share/opencode/log/opencode.log` fallback (never a hardcoded home path). It MUST be best-effort: missing/unreadable/rotated/truncated log, unparseable lines, or an unknown session id degrade silently to reporting nothing. It must not block, must not raise into the turn, and must be bounded: open at the current end-of-file and read forward only, never re-reading the 148MB history, and tolerating concurrent appends from other opencode processes on the same machine.
  - Depends on: E-01
  - Expected outcome: given a fixture log with progress lines attributable to our turn the observer reports progress timestamps; given unattributable lines, background-noise-only lines, or an unreadable log it reports nothing and raises nothing.
  - Execution state: performed

- [x] E-03 Wire the observer into the turn loop in `oc_runipd.py` so it `touch()`es BOTH `heartbeat` and `watchdog` on observed progress, alongside the existing stdout touches at oc_runipd.py:1775-1776. Record which source last showed progress (`stdout` or `subagent`) so the display can name it. Start and stop the observer with the same `with heartbeat, watchdog:` scope so it cannot outlive the turn or leak a thread across attempts. Do NOT change the timeout value and do NOT alter the kill path.
  - Depends on: E-02
  - Expected outcome: a turn that emits no stdout but whose attributable subagent is active is NOT killed at the timeout; the watchdog's idle clock resets from observed progress; no observer thread survives the turn.
  - Execution state: performed

### Task group 2: honest countdown display

- [x] E-04 Change `render_stream.Heartbeat` (render_stream.py:228-274) so its line states the countdown and the progress source instead of only "still working": report time since last OBSERVED PROGRESS and the remaining time until the stall kill, and name the source of the last progress. The countdown MUST derive from the watchdog's own clock (the authority that kills), not a second independent timestamp, so the displayed number cannot disagree with reality; today `Heartbeat._last_activity` (render_stream.py:239) and `StallWatchdog._last_activity` (oc_runipd.py:148) are independent. When no stall timeout is configured (`--stall-timeout 0`, watchdog disabled) the line must omit the countdown rather than print a false or infinite one. Keep it a single short stderr line in the existing conventions (no color dependence for meaning).
  - Depends on: E-03
  - Expected outcome: during a quiet stretch the user sees a shrinking time-to-kill sourced from the watchdog and whether progress came from stdout or a subagent; with the watchdog disabled no countdown is claimed.
  - Execution state: performed

- [x] E-05 Eliminate the duplicate Heartbeat so the honest display cannot be silently absent from `aw agy run`: `agy_runipd.Heartbeat` (agy_runipd.py:247-296) is a byte-identical copy of the shared class and agy does not import `render_stream` at all. Replace the agy copy with an import of `render_stream.Heartbeat` (the same pattern oc_runipd already uses, oc_runipd.py:39-51), and extend the existing single-definition guard in `tests/test_render_stream.py` (which today covers only oc_runipd, :292) to assert agy has no inline `class Heartbeat:` either. This is display-only unification of an already-identical class; it does NOT unify the runners (backlog `dhuape`) and must not change agy's watchdog wiring, which already receives subagent events on stdout (agy_runipd.py:234-243).
  - Depends on: E-04
  - Expected outcome: exactly one `Heartbeat` definition exists in the codebase, both drivers import it, and `aw agy run` shows the same honest countdown line; agy's stall behavior is otherwise unchanged.
  - Execution state: performed

### Task group 3: prove the kill guarantee survives

- [x] E-06 Add the true-hang preservation tests that prove this change did not make a hang immortal, in BOTH variants: (a) a SILENT hang (no stdout, no log lines) and (b) a NOISY hang (no stdout, no agent-loop progress, but background lines for our own process still arriving, as a real permission deadlock produces - backlog `qyaime`). Both must still terminate at the timeout and record `ipd-stalled`. Write these as first-class tests of the shipped behavior, not as an afterthought: variant (b) is the specific regression this plan risks introducing, since a too-permissive attribution turns a recoverable kill into an unrecoverable immortal run.
  - Depends on: E-03
  - Expected outcome: both hang variants are killed at the timeout with `ipd-stalled` recorded, with the observer active and reading a log that is receiving noise.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `StallWatchdog` (oc_runipd.py:132-167) is a daemon thread comparing `time.monotonic() - self._last_activity` against `self.timeout`, terminating the child via `terminate_process`. `touch()` is the only way to reset it, and it is called from exactly two places (oc_runipd.py:1775-1776), both inside `for line in process.stdout`. It exposes `timeout`, `enabled`, and `stalled`, but no "remaining time" accessor - E-04 needs one (or an equivalent) for a truthful countdown.
- `DEFAULT_STALL_TIMEOUT = 600.0` (oc_runipd.py:1629); it is already overridable per run via `options["stall_timeout"]` / `--stall-timeout`, so the fix does not need a new knob. `0` DISABLES the watchdog (`self.enabled = self.timeout > 0`), a case the countdown display must handle.
- `Heartbeat` is NOT actually shared: `render_stream.Heartbeat` (render_stream.py:228-274) is imported by oc_runipd (oc_runipd.py:39-51), but `agy_runipd.py` carries a byte-identical inline copy (agy_runipd.py:247-296) and does not import `render_stream` at all (`grep -c render_stream agent_workflows/agy_runipd.py` = 0). A display change in render_stream therefore does NOT land once. `tests/test_render_stream.py:255-297` guards oc_runipd against an inline copy but says nothing about agy.
- The oc child stdout event vocabulary is only `step_start`/`step_finish`/`text`/`tool_use` (tallied across recent `sessions/*.jsonl`) and every event carries the PARENT `sessionID`; there is no subagent-progress event, which is why an out-of-band signal is required for the opencode driver.
- The agy child stream is different: `render_agy_event` already handles `step_type == "subagent"` (agy_runipd.py:234-243), so agy's watchdog already sees subagent activity. The two drivers are NOT symmetric here.
- The driver captures the turn's opencode session id via `extract_session_id` (oc_runipd.py:1383-1402), reading `sessionID`/`sessionId`/`session_id` from the streamed JSONL - but only AFTER the turn's log is written, and the accessible id is the PARENT session. Live in-turn attribution therefore needs either an incremental read of the same stdout log or the `created ... parentID=` route; E-01 must settle this rather than assume it.
- opencode's log line format is `timestamp=<ISO> level=INFO run=<8hex> message=<kind> [session.id=ses_...] ...` - `run=` is a per-CLI-process token shared by a parent turn and its subagent sessions, while `session.id=` distinguishes them.
- The leak sanitizer treats a real `ses_...` token as a finding (rule `session-id`, leak_sanitizer.py:80-81), so committed log fixtures must be redacted; `aw sanitize --agent` is the deterministic check to run.

## Findings

- ROOT CAUSE: the stall decision is stdout-only, and `opencode run --format json` stdout carries ONLY parent-session events. Work that produces no parent-session event (subagent/Task delegation being the clearest case) is invisible, so "no stdout" is wrongly equated with "no progress".
- EVIDENCE (the blind spot, REPRODUCED LIVE): a controlled `opencode run --print-logs --format json --auto` invocation that delegates to a Task/subagent shows the gap directly. Parent stdout emitted 7 events total, with a 24.6s silence from `text` at 15:41:13.851 to `tool_use task` at 15:41:38.476. Across exactly that window, opencode's log shows the subagent session `session.id=<child>` advancing steps 1->4 (15:41:18.387, :23.436, :27.990, :38.426) plus `message=evaluated permission=...` lines for its tool calls. So the parent's stdout is silent for the whole subagent lifetime while the subagent works. Scale that 24.6s gap past 600s and the watchdog kills a progressing turn. (Reproduction command and full timeline are the E-01/V-01 fixture basis; the log lines are transient, so the fixture must be a COMMITTED, session-id-redacted capture, not a reference to a live log.)
- EVIDENCE (the kills are real and recurring): 4 `ipd-stalled` events on 2026-08-29 across two runs (`grep -rh ipd-stalled .aw/records/runs/*/events.jsonl`): w0ln4q at 14:33:40, qcqhj7 15:00:27, rchpms 15:10:31, 7p9n2v 15:20:36, all `stall_timeout: 600.0`.
- CORRECTION (a prior draft of this plan misread its own evidence; recorded so the error is not repeated): the w0ln4q incident is NOT a verified subagent false positive. Its last stdout event is a COMPLETED `bash` tool call (`cat .aw/records/releases/README.md; ...`) at 14:23:40, and NO `task` tool_use appears anywhere in `sessions/01-w0ln4q-attempt-1.jsonl` (11 tool_use events: read/bash/todowrite only). The `ses_fb2186...` child session cited as "our subagent" was created 14:23:39.662 with a title naming an `@explore` subagent, but attributing it to the w0ln4q turn was an inference, and after 14:30:19.517 that CLI process (`run=08f2d537`) emitted NOTHING at all until the 14:33:40 kill - so even the log shows a >3-minute total silence before the kill, which the proposed observer would NOT have prevented. Three of the four kills (qcqhj7, rchpms, 7p9n2v) have ZERO-BYTE stdout logs - the child never emitted a single event, a different failure mode (likely launch/permission blockage, cf. backlog `qyaime`) that a subagent-progress observer also does not address. NET: the stdout-only defect is real and reproduced, but the specific incidents cited do not prove the subagent variant, and the observer alone would not have saved any of the four recorded kills.
- EVIDENCE (true positive, must be preserved): backlog `qyaime` documents a worktree-isolated `--auto` turn logging `message=asking ... permission=external_directory patterns=["<repo-root>/*"]` with no answerer and then producing nothing; the watchdog correctly ended it. NOTE this hang mode is NOT log-silent - the blocked CLI process may still emit `message=evaluated`/`llm runtime selected` background lines - so a naive "any log line for our process" observer would DEFEAT true-hang detection. The observer's attribution must count only genuine agent-loop progress (e.g. `message=loop`/`message=process`/`message=stream` for a session belonging to our process), never permission-evaluation or housekeeping lines. This constraint is load-bearing, not advisory.
- ATTRIBUTION MECHANISM (the prior draft's key was wrong; corrected and resolved in review - see OQ-02): `parentID=` is NOT usable for ongoing progress. In a 20MB log slice, `parentID=ses_` appears on only 23 lines and every one is a `message=created` line (or an unrelated command echo); of the 235 log lines for a known child session, ZERO carry `parentID`. Ongoing child lines carry `session.id=<child>` only, with no reference to the parent. THE RESOLVED KEY is the two-hop parent-session route: the driver reads its own parent session id off the FIRST stdout event (live reproduction: parent `step_start` at 15:41:12.423 carries it, 6.6s before the subagent's `created` line at 15:41:13.806, so the key is available in time), matches `message=created ... parentID=<our parent id>` to learn each child id, then counts that child's `session.id=<child>` agent-loop lines. The alternative `run=<id>` per-process token IS shared by parent and subagent (`run=d5504c8d` on both in the reproduction) but the driver cannot learn its child's `run=` id, so it is rejected as the primary key.
- PROGRESS vs NOISE (load-bearing for true-hang preservation): count ONLY `message=loop`/`message=process`/`message=stream` for an attributed session. In a 5MB slice, the non-session-attributed line population is dominated by housekeeping (`message=evaluated permission` 7435, `message=tracking hash` 4189, `message="llm runtime selected"` 2114, `message="resolved path"` 1619, `message=asking` 94), and a permission-blocked process keeps producing exactly those. Counting them would make a deadlocked run immortal.
- The heartbeat's current wording actively misleads: it says "still working" while a kill countdown runs, which is why a stalled-but-doomed turn is indistinguishable from a doomed one at a glance. Note the countdown is only truthful if it reflects the SAME clock the watchdog uses; the Heartbeat and StallWatchdog currently keep independent `_last_activity` timestamps (render_stream.py:239, oc_runipd.py:148), so the display must read the watchdog's remaining time rather than computing its own.
- DUPLICATE HEARTBEAT: `render_stream.Heartbeat` (render_stream.py:228-274) and `agy_runipd.Heartbeat` (agy_runipd.py:247-296) are byte-identical apart from the docstring; agy does NOT import render_stream (`grep -c render_stream agent_workflows/agy_runipd.py` = 0). `tests/test_render_stream.py:292` asserts oc_runipd has no inline copy but nothing constrains agy. So a display fix in render_stream alone silently leaves `aw agy run` printing the misleading line.
- AGY DOES NOT HAVE THIS BUG: `render_agy_event` handles `step_type == "subagent"` (agy_runipd.py:234-243), i.e. agy's stdout stream already reports subagent activity, and every stdout line already touches the watchdog (agy_runipd.py:1844-1845). Adding a log observer to agy would be unfounded scope.
- HONEST LIMIT: reading opencode's log is coupling to another tool's internal artifact - format/location may change across versions. Hence it MUST be best-effort and degrade to today's behavior, and the fixture pins the observed version (1.18.25, from the `created ... version=` line). The log path itself must be resolved from `XDG_DATA_HOME` with the `~/.local/share/opencode/log/opencode.log` fallback, never hardcoded to a home path.
- SECURITY/LEAK CONSTRAINT: real opencode session ids are a leak-sanitizer finding. `agent_workflows/leak_sanitizer.py:81` defines rule `session-id` as `\bses_(?!<redacted>)[0-9A-Za-z]{8,}`, and a probe repo containing a fixture line with a `ses_...` token is flagged (`{"rule":"session-id","location":"test_fix.py:1"}`, exit 1). Therefore any committed log fixture MUST use redacted/synthetic session tokens, and the observer must never write a raw session id into a committed artifact or the heartbeat line.
- PERFORMANCE/OPERABILITY: the live log is 148MB and shared by every concurrent opencode process on the machine. Tailing must be offset-bounded (already required) AND must tolerate concurrent appends, truncation/rotation, and interleaved lines from unrelated runs. The observer thread must also not add a per-line parse cost that scales with total machine activity rather than our turn.

### E-01 CONFIRMATION (recorded 2026-08-30, opencode 1.18.25 as installed)

The two-hop parent-session route and the loop/process/stream classification BOTH HOLD on the installed version.
No REPLAN is required. Full commands and output are pasted under V-01; the load-bearing results are:

- `opencode --version` -> `1.18.25` (matches the version this plan pins). Log resolved from the environment
  (`XDG_DATA_HOME` unset -> `~/.local/share/opencode/log/opencode.log`, 173499622 bytes / ~165MB, i.e. the
  148MB figure has since grown, reinforcing that tailing must be offset-bounded).
- REJECTED KEY RE-DISPROVEN: for a real subagent session with 108 log lines, exactly ONE carried `parentID`, and
  that line was the `message=created` line; ZERO ongoing lines carried it. Ongoing child lines carry only
  `session.id=<child>`.
- CHOSEN ROUTE CLOSES END-TO-END ON A REAL DRIVER TURN: the parent session id taken from the FIRST stdout event
  of `run-20260830T064736Z-3251543/sessions/02-plqjt7-attempt-1.jsonl` MATCHED a live
  `message=created ... parentID=<that id>` line, and the parent id was available 80.2s BEFORE the child spawned
  (07:27:36.588Z vs 07:28:56.790Z), so the key is obtainable in time.
- `run=` IS shared by parent and subagent (`run=74347d25` on both), confirming the rejected alternative's premise
  while it stays rejected because the driver cannot learn its child's `run=` id.
- CLASSIFICATION CONFIRMED: in a 3MB slice the housekeeping population dwarfs progress
  (`evaluated` 4174, `tracking` 2567, `llm runtime selected` 1290, `resolved path` 1087, `touching` 292,
  `asking` 97) while agent-loop kinds are `loop` 1290 / `stream` 1290 / `process` 1289. A permission-deadlocked
  process keeps producing the former, which is exactly why only the latter may count.
- THE SHIPPED PARSER WAS THEN REPLAYED AGAINST THE LIVE LOG (not only the fixture) and found the real child and
  its progress: `polls: 41  children: 1  progress: 106`.

CORRECTION TO THE PLAN'S OWN PREMISE, found during execution and recorded as DECISION 06-kaga7s-D1: the plan's
E-04/E-05 describe `Heartbeat` as the live quiet-turn display, but commit `b62e7634` (2026-08-29 22:22, AFTER
this plan was reviewed) replaced it with `Statusline` in BOTH drivers, and `Heartbeat` is now instantiated
NOWHERE in production code. The plan's cited line numbers (`render_stream.py:228-274`, `oc_runipd.py:1775-1776`)
no longer resolve to those constructs. The honest countdown was therefore implemented on BOTH the live
`Statusline` and `Heartbeat`, sourced from one new authority (`StallWatchdog.remaining()`), so the plan's GOAL
(an operator sees the real countdown) is met rather than only its letter.

REPRODUCED BLIND SPOT ON REAL TURNS (measured stdout silence within turns that used subagents):
`02-plqjt7-attempt-1` 570 events, largest gaps 34.2/52.9/55.9/96.3/110.7/246.5s;
`08-ovbnyq-attempt-1` 380 events, largest gaps 110.2/113.8/118.1/120.1/282.7s. A 246.5s stdout silence on a
healthy turn is 41% of the 600s budget, so the timeout is demonstrably measuring the wrong thing.

## Proposed changes (ordered, validatable)

1. Establish and record the attribution mechanism from evidence (the prior draft's `parentID` key is disproven); decide the progress-line classification that keeps a noisy hang detectable.
2. New shared progress observer: tail opencode's log from the current end-of-file, report progress only for attributable agent-loop lines; log path from `XDG_DATA_HOME`; fully best-effort.
3. `oc_runipd.py`: touch heartbeat+watchdog from the observer as well as stdout; track last-progress source; observer lifetime bound to the turn scope.
4. `render_stream.Heartbeat`: state time-since-progress, time-to-kill derived from the WATCHDOG's clock, and the progress source; omit the countdown when the watchdog is disabled.
5. `agy_runipd.py`: delete the duplicate `Heartbeat` copy and import the shared one, so the honest line is not missing from `aw agy run`. No observer and no watchdog-wiring change for agy (it already gets subagent events on stdout).
6. `tests/`: BOTH true-hang preservation variants (silent and noisy) as first-class tests, plus the stdout-silence regression, best-effort degradation, offset-boundedness, thread hygiene, leak-clean fixture, and the display assertions.

## Deferred / out of scope (with reason)

- Fixing the upstream opencode permission-prompt hang: not ours to fix; tracked by backlog `qyaime` (which also gates the 2.0.0 release). This plan makes the driver survive and correctly classify it, and V-06(b) is the assertion that this plan does not make `qyaime`'s hang undetectable.
- A PROGRESS OBSERVER FOR THE AGY DRIVER: deliberately NOT done, and this is a scope CORRECTION rather than an omission. `agy --output-format stream-json` already emits `step_type == "subagent"` events on stdout (agy_runipd.py:234-243) and every stdout line already touches the watchdog (agy_runipd.py:1844-1845), so agy has no subagent blind spot to fix. Only the DISPLAY change reaches agy (E-05). Should agy later prove to have its own blind spot, that is a separate plan with its own evidence.
- THE ZERO-EVENT KILLS (qcqhj7, rchpms, 7p9n2v on 2026-08-29): three of the four recorded `ipd-stalled` kills have zero-byte stdout logs, meaning the child produced no event at all. That is a different defect (launch/permission blockage, cf. backlog `qyaime`) and is NOT addressed here; this plan must not be described or validated as fixing them. If they are not already covered by `qyaime`, file a backlog item; do not widen this plan.
- Raising or removing `DEFAULT_STALL_TIMEOUT`: deliberately NOT done. Raising it would delay real-hang detection and does not fix the wrong signal; the timeout stays 600s and becomes meaningful once progress is measured correctly.
- Emitting subagent progress into the run ledger (`events.jsonl`) for `aw runs` visibility: valuable but separate reporting work; tracked by backlog `em0z50` (per-artifact disposition lines + end-of-run summary).
- Broader unification of the two drivers: backlog `dhuape`. E-05 collapses only the already-identical `Heartbeat` class (a display fix that must reach both drivers); it does NOT extract a shared runner library and must not grow into one.

## Scope check

- Over-scope (FOUND AND REMOVED in review): the prior draft's E-03 added the progress observer to `agy_runipd.py`. That was unfounded - agy already receives `step_type == "subagent"` events on stdout (agy_runipd.py:234-243), so it has no blind spot to fix, and the claim that "fixing only oc would leave `aw agy run` killing healthy turns" is contradicted by the code. Replaced with E-05, which reaches agy only for the DISPLAY fix (the genuine cross-driver gap, since agy carries a duplicate `Heartbeat`).
- Under-scope (FOUND AND ADDED in review): (a) the attribution mechanism was assumed rather than established, and the assumed key is disproven, so E-01 now establishes it before code; (b) nothing forced the countdown to agree with the watchdog's own clock, so a plausible implementation could print a confident but wrong number; (c) the noisy-hang variant of true-hang preservation was missing, which is the one case where this fix could plausibly break the kill guarantee; (d) the committed-fixture leak risk (real session ids) was unaddressed; (e) thread lifetime and the `--stall-timeout 0` display case were unspecified.
- Residual scope risk: E-05 touches a second driver. It is bounded to deleting a byte-identical class and adding an import, and V-05 asserts agy's stall behavior is unchanged.

## Required tests / validation

- ATTRIBUTION MECHANISM RECORDED: the chosen key and the progress-line classification are evidenced, and the disproven `parentID`-on-ongoing-lines assumption is documented (V-01).
- STDOUT-SILENCE REGRESSION (the bug): stdout goes quiet while an attributable subagent is active -> turn survives, no `ipd-stalled`. Must fail before the fix.
- TRUE-HANG PRESERVATION, BOTH VARIANTS: (a) silent - no stdout, no log lines -> still killed, `ipd-stalled` recorded. (b) NOISY - no stdout, no agent-loop progress, but our process still emitting `message=evaluated permission=...` / housekeeping lines -> STILL killed. Variant (b) is the guarantee that the observer did not turn a permission deadlock (backlog `qyaime`) into an immortal run.
- ATTRIBUTION NEGATIVES: a different session/process does not count as our progress; background-noise lines for our own process do not count as progress.
- DEGRADATION: missing / unreadable / garbage / mid-line-truncated log -> observer returns nothing, raises nothing, watchdog behaves as today.
- BOUNDEDNESS: observer reads from its start offset only (no full re-read of a 148MB log) and tolerates concurrent appends.
- THREAD HYGIENE: no observer thread outlives the turn.
- LEAK-CLEAN FIXTURE: committed fixtures contain no real `ses_` token; `aw sanitize --agent` is clean.
- DISPLAY: heartbeat shows time-since-progress + a DECREASING time-to-kill sourced from the WATCHDOG's clock + the progress source; no countdown claimed when the watchdog is disabled; bare "still working" gone.
- SINGLE HEARTBEAT: exactly one `Heartbeat` definition; agy imports it; the honest line appears in `aw agy run` too.

Validation command: `python3 -m pytest tests/test_stall_progress.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_render_stream.py -q` plus a full default suite `python3 -m pytest -p no:randomly` (paste ACTUAL output; never claim success unrun). Also `aw sanitize --agent` for the fixture leak check.

## Spec / documentation sync

- Update the `--stall-timeout` CLI help for the OPENCODE driver (oc_runipd.py:2799-2804) to say the timeout measures time since last observed progress (stdout OR subagent), not merely stdout silence. Leave the agy help text (agy_runipd.py:2836-2840) accurate for agy, which remains stdout-only by design (its stdout already carries subagent events) - do not copy a claim the agy driver does not implement.
- Note the best-effort opencode-log coupling near the observer so a future reader knows it is an optional signal, not a contract, and record the pinned observed format version there.
- Document, next to the observer, the noisy-hang constraint (why only agent-loop lines count) so a later "simplification" to "any log line" cannot silently destroy true-hang detection.

## Open questions

### OQ-01: Should the driver depend on opencode's internal log at all, or wait for an upstream subagent-progress event on stdout?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Use the log now, as a BEST-EFFORT signal only. Waiting for upstream is not viable: the failure is active and expensive (4 recorded `ipd-stalled` kills on 2026-08-29 alone), and we do not control opencode's release cadence. The coupling risk is real but bounded by the fail-safe rule - if the log's location or format changes, the observer yields nothing and we degrade to exactly today's behavior rather than breaking. If opencode later emits subagent progress on stdout, that becomes a second progress source and the log observer can be dropped without changing the watchdog contract. (Reviewed 2026-08-29: this resolution survives, but note it was originally written alongside a WRONG attribution key; using the log is still the right call, HOW to attribute a line is now OQ-02.)

### OQ-02: What is the correct in-process attribution key, and can the driver actually obtain it at turn start?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-5-1m-us (/plan-review)
- Resolution or deferral rationale: RESOLVED as route (a), the two-hop parent-session route, and the original key is REJECTED. REJECTED: `parentID` on ongoing child lines does not exist - in a 20MB log slice every `parentID=ses_` occurrence sits on a one-shot `message=created` line, and a known child session's 235 ongoing lines carry ZERO `parentID` (they carry only `session.id=<child>`). CHOSEN (route a): the driver learns its OWN parent session id from the FIRST stdout event (every stdout event carries the parent `sessionID`; live reproduction: the first `step_start` arrives at 15:41:12.423 carrying the parent id, 6.6s BEFORE the subagent's `created` line at 15:41:13.806), then scans the log for `message=created ... parentID=<our parent id>` to learn each child session id, then counts that child's subsequent `session.id=<child>` agent-loop lines as progress. This needs no new plumbing and no knowledge of the `run=` token. Route (b) (`run=<id>`) is confirmed to co-identify parent and subagent (`run=d5504c8d` on both) but is REJECTED as the primary key because the driver has no way to learn its child's `run=` id, and because `run=` is per-CLI-process, making it coarser than needed. PROGRESS-LINE CLASSIFICATION (the true-hang-preserving half): count ONLY `message=loop` / `message=process` / `message=stream` for an attributed session; explicitly EXCLUDE `message=evaluated`, `message=asking`, `message="llm runtime selected"`, `message=tracking`, `message="resolved path"`, `message="touching file"`, and all other housekeeping, because a permission-deadlocked process keeps emitting those (this is exactly what V-06(b) asserts). E-01 remains in the plan to CONFIRM this against the running version and record the evidence, and its REPLAN escape hatch remains in force if confirmation fails.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: The recorded CONFIRMATION, pasted into this plan's Findings, citing the ACTUAL commands and output (not reasoning alone): (a) a `message=created ... parentID=<parent>` line for a real subagent spawn, (b) that child's ongoing `session.id=` lines showing NO `parentID` (the disproof of the rejected key, re-confirmed on the installed version), (c) the parent's first stdout event carrying the parent `sessionID` with a timestamp EARLIER than the child's `created` line (proving the key is available in time), and (d) the `message=` kind tally distinguishing agent-loop lines from housekeeping. Session ids in the pasted evidence must be redacted. If confirmation fails, the required evidence is that finding plus a REPLAN recommendation.
  - Observed evidence: CONFIRMED on the installed version. `opencode --version` -> `1.18.25`, matching the
    version the plan pins. Log resolved from the environment (`XDG_DATA_HOME` unset ->
    `~/.local/share/opencode/log/opencode.log`, 173499622 bytes).

    (a) A REAL subagent spawn (last such line in the live log; session ids redacted):
    ```
    timestamp=2026-08-30T07:28:56.790Z level=INFO run=74347d25 message=created id=ses_<CHILD> slug=crisp-mountain
      version=1.18.25 projectID=449edf33... directory=<repo>/.aw/worktrees/plqjt7 path="" workspaceID=undefined
      parentID=ses_<PARENT> title="Find lane branch integration convention (@explore subagent)" agent=explore
    ```
    Across the whole log, `grep -c 'parentID=ses_'` = 349 real spawns, so this shape is not a one-off.

    (b) DISPROOF of the rejected `parentID` key, re-confirmed on 1.18.25. For that child session:
    ```
    total child lines:                            108
    child lines with parentID:                      1
      (that one line is message=):          message=created
    child ONGOING (non-created) lines w/ parentID:  0
    ```
    So an ongoing child line carries ONLY `session.id=`, never `parentID`, exactly as OQ-02 concluded.
    Sample ongoing lines (redacted):
    ```
    timestamp=2026-08-30T07:28:56.851Z level=INFO run=74347d25 message=loop    session.id=ses_<CHILD> step=0
    timestamp=2026-08-30T07:28:57.067Z level=INFO run=74347d25 message=process session.id=ses_<CHILD> messageID=msg_...
    timestamp=2026-08-30T07:28:57.068Z level=INFO run=74347d25 message=stream  ... session.id=ses_<CHILD> ... mode=subagent
    ```

    (c) THE KEY IS AVAILABLE IN TIME, and the two-hop route CLOSES END-TO-END on a real driver turn. I took the
    parent session id from the FIRST stdout event of a real run
    (`.aw/records/runs/run-20260830T064736Z-3251543/sessions/02-plqjt7-attempt-1.jsonl`) and matched it against the
    log's `parentID=`:
    ```
    FIRST stdout event: type=step_start timestamp=2026-08-30T07:27:36.588Z sessionID=ses_<PARENT>
    MATCH: is the spawn's parentID our turn's stdout sessionID?  YES - two-hop route closes end-to-end
    parent 1st stdout event : 2026-08-30T07:27:36.588Z   (carries parent sessionID)
    child  created line     : 2026-08-30T07:28:56.790Z
    => parent id available 80.2s BEFORE the child spawns
    ```
    Also confirmed the rejected alternative's premise: `run=` IS shared by parent and child
    (`parent runs: run=74347d25` / `child runs: run=74347d25`), but the driver cannot learn the child's `run=`
    id, which is why the two-hop route is used instead.

    (d) `message=` KIND TALLY separating agent-loop from housekeeping (3MB live slice, 13868 lines):
    ```
       4174 message=evaluated          <- housekeeping (a permission-deadlocked process keeps emitting this)
       2567 message=tracking           <- housekeeping
       1290 message=stream             <- AGENT-LOOP PROGRESS
       1290 message=loop               <- AGENT-LOOP PROGRESS
       1290 message="llm               <- housekeeping ("llm runtime selected")
       1289 message=process            <- AGENT-LOOP PROGRESS
       1087 message="resolved          <- housekeeping
        292 message="touching          <- housekeeping
         97 message=asking             <- housekeeping (THE DEADLOCK LINE, backlog qyaime)
    ```
    And on the child's OWN lines the population is almost entirely agent-loop
    (`36 loop`, `35 stream`, `35 process`, `1 exiting`, `1 created`), confirming the allowlist captures real
    subagent work while excluding the chatter a hung process produces.

    THE BLIND SPOT ITSELF, reproduced from real driver logs (this is what the observer fixes): measured stdout
    silence gaps within single turns that DID use subagents:
    ```
    run-20260830T064736Z-3251543/sessions/02-plqjt7-attempt-1.jsonl  570 events, largest gaps (s): [34.2, 52.9, 55.9, 96.3, 110.7, 246.5]
    run-20260828T002915Z-3129108/sessions/08-ovbnyq-attempt-1.jsonl  380 events, largest gaps (s): [110.2, 113.8, 118.1, 120.1, 282.7]
    ```
    A 246.5s stdout silence on a healthy turn is already 41% of the 600s budget, so the mechanism that kills at
    600s is demonstrably firing on the wrong signal.

    FINAL CONFIRMATION that the shipped parser handles the LIVE format (not just the fixture): replaying the real
    log through the built observer with the real parent id found the real child and its progress:
    ```
    polls: 41  children: 1  progress: 106
    ```
    No REPLAN is required: the two-hop route and the progress/noise classification both hold on 1.18.25.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted output of a named unit test (e.g. `tests/test_stall_progress.py`) that feeds the observer a COMMITTED fixture log pinned to the observed opencode format (version 1.18.25) with all session tokens REDACTED/synthetic. The fixture must contain the real reproduced shape: a `created id=<child> ... parentID=<our session>` line, subsequent child `message=loop`/`process`/`stream` lines, unrelated lines for a DIFFERENT session/process, and background-noise lines (`message=evaluated permission=...`, `message="llm runtime selected"`). Assert progress IS reported for our attributable agent-loop lines, and NOT for the unrelated session, NOT for the noise-only lines. Plus degradation cases each asserting "returns nothing, raises nothing": missing file, unreadable/permission-denied file, garbage/truncated lines, and a mid-line truncated tail. Plus an offset-boundedness assertion using a pre-seeded large fixture, proving pre-start content is never read. Plus a pasted `aw sanitize --agent` (or `python3 -m agent_workflows check-local-leaks . --agent`) run showing `outcome":"clean"` with the fixture committed, proving no real `ses_` token leaked (rule `session-id`, leak_sanitizer.py:81).
  - Observed evidence: New module `agent_workflows/stall_progress.py`; committed fixture
    `tests/fixtures/opencode-subagent-progress.log` (pinned `version=1.18.25`, all session tokens in the
    sanitizer-approved `ses_<redacted>...` form, containing the real reproduced shape: our
    `created ... parentID=<our parent>` spawn, the child's `loop`/`process`/`stream` lines, an UNRELATED
    session under a different `run=`, and housekeeping noise).

    `python3 -m pytest tests/test_stall_progress.py -p no:randomly -v -o addopts=""`:
    ```
    tests/test_stall_progress.py::LogPathResolutionTests::test_falls_back_to_local_share PASSED [  4%]
    tests/test_stall_progress.py::LogPathResolutionTests::test_honors_xdg_data_home PASSED [  8%]
    tests/test_stall_progress.py::LogPathResolutionTests::test_module_has_no_hardcoded_home_path PASSED [ 12%]
    tests/test_stall_progress.py::ProgressClassificationTests::test_agent_loop_kinds_are_progress PASSED [ 16%]
    tests/test_stall_progress.py::ProgressClassificationTests::test_housekeeping_kinds_are_not_progress PASSED [ 20%]
    tests/test_stall_progress.py::ProgressClassificationTests::test_progress_kinds_are_a_closed_allowlist PASSED [ 24%]
    tests/test_stall_progress.py::AttributionTests::test_does_not_report_progress_for_a_different_session PASSED [ 28%]
    tests/test_stall_progress.py::AttributionTests::test_noise_only_log_reports_no_progress PASSED [ 32%]
    tests/test_stall_progress.py::AttributionTests::test_parent_learned_late_still_attributes PASSED [ 36%]
    tests/test_stall_progress.py::AttributionTests::test_reports_progress_for_our_attributable_subagent PASSED [ 40%]
    tests/test_stall_progress.py::AttributionTests::test_set_parent_session_rejects_junk PASSED [ 44%]
    tests/test_stall_progress.py::AttributionTests::test_unrelated_child_is_never_added_even_with_a_known_parent PASSED [ 48%]
    tests/test_stall_progress.py::DegradationTests::test_garbage_log_returns_nothing_raises_nothing PASSED [ 52%]
    tests/test_stall_progress.py::DegradationTests::test_mid_line_truncated_tail_is_not_misparsed PASSED [ 56%]
    tests/test_stall_progress.py::DegradationTests::test_missing_log_returns_nothing_raises_nothing PASSED [ 60%]
    tests/test_stall_progress.py::DegradationTests::test_truncation_reanchors_without_crashing PASSED [ 64%]
    tests/test_stall_progress.py::DegradationTests::test_unreadable_log_returns_nothing_raises_nothing PASSED [ 68%]
    tests/test_stall_progress.py::BoundednessTests::test_pre_start_content_is_never_read PASSED [ 72%]
    tests/test_stall_progress.py::BoundednessTests::test_tolerates_concurrent_appends_across_polls PASSED [ 76%]
    tests/test_stall_progress.py::PollerThreadHygieneTests::test_a_raising_sink_does_not_break_the_poller PASSED [ 80%]
    tests/test_stall_progress.py::PollerThreadHygieneTests::test_poller_touches_registered_sinks_on_progress PASSED [ 84%]
    tests/test_stall_progress.py::PollerThreadHygieneTests::test_repeated_attempts_do_not_accumulate_threads PASSED [ 88%]
    tests/test_stall_progress.py::PollerThreadHygieneTests::test_thread_does_not_outlive_the_context PASSED [ 92%]
    tests/test_stall_progress.py::FixtureHygieneTests::test_fixture_contains_no_unredacted_session_id PASSED [ 96%]
    tests/test_stall_progress.py::FixtureHygieneTests::test_fixture_pins_the_observed_opencode_version PASSED [100%]
    ============================== 25 passed in 1.73s ==============================
    ```
    Mapping to each required assertion: progress IS reported for our attributable lines
    (`test_reports_progress_for_our_attributable_subagent`); NOT for the unrelated session
    (`test_does_not_report_progress_for_a_different_session`, `test_unrelated_child_is_never_added_even_with_a_known_parent`);
    NOT for noise-only (`test_noise_only_log_reports_no_progress`, `test_housekeeping_kinds_are_not_progress`);
    all four degradation cases (`test_missing_log_...`, `test_unreadable_log_...`, `test_garbage_log_...`,
    `test_mid_line_truncated_tail_is_not_misparsed`, plus `test_truncation_reanchors_without_crashing`);
    offset-boundedness against a pre-seeded >100KB fixture containing attributable progress that must NOT be
    read (`test_pre_start_content_is_never_read`); and no hardcoded home path
    (`test_module_has_no_hardcoded_home_path`).

    LEAK CHECK with the fixture tracked (`git add -N` then `aw sanitize --agent`):
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    EXIT=0
    ```
    NOTE on a real detail this surfaced: because the fixture MUST use `ses_<redacted>` (a realistic token is a
    `session-id` finding), the parser's session-token pattern accepts `<`/`>`/`-` so ONE code path serves both the
    live log and the fixtures (no fixture-only branch that could diverge). Verified the same parser still handles
    genuine unredacted tokens: `_CREATED_RE` on a real-shaped line yielded
    a correctly split `child=ses_<redacted>` / `parent=ses_<redacted>` pair, and `classify_progress` on a real `message=loop` line
    returned `loop`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: THE REGRESSION, pasted: a test that drives a fake child which emits stdout events and then goes silent on stdout, while a fixture log shows attributable agent-loop progress continuing, with a SHORT `stall_timeout` (e.g. 2s) so the test is fast. Assert the turn is NOT terminated and no `ipd-stalled` event is recorded. It MUST fail before the fix and pass after (paste both runs, or the failure output plus the pass). Plus a test asserting the recorded last-progress source is `subagent` in that case and `stdout` when stdout is active. Plus a thread-hygiene assertion: after the turn returns, no observer thread remains alive (e.g. compare `threading.enumerate()` before and after, pasted).
  - Observed evidence: THE REGRESSION is
    `tests/test_stall_progress_integration.py::SubagentProgressSurvivalTests::test_turn_with_quiet_stdout_but_active_subagent_is_not_killed`.
    It launches the REAL driver (`python3 -m agent_workflows.oc_runipd start ... --stall-timeout 0.7`) against a
    fake `opencode` that emits two stdout events (so the driver learns the parent session id), then goes SILENT on
    stdout for ~2.4s (3.4x the timeout) while writing attributable `created`/`loop`/`process` lines into the log
    that `XDG_DATA_HOME` resolves to.

    FAILS BEFORE THE FIX. I mutated ONLY the observer's touch of the watchdog back to pre-fix stdout-only
    behavior (`def _subagent_progress(): pass`) and re-ran:
    ```
    === MUTATION APPLIED: observer no longer touches the watchdog (pre-fix behavior) ===
    E   AssertionError: Lists differ: [{'at': '2026-08-30T09:33:34+00:00', 'atte[67 chars]0.7}] != []
    E   First extra element 0:
    E   {'at': '...', 'attempt': 1, 'event': 'ipd-stalled', 'id6': 'prog01', 'stall_timeout': 0.7}
    E    : a PROGRESSING turn was killed: subagent progress did not reach the watchdog
    FAILED tests/test_stall_progress_integration.py::SubagentProgressSurvivalTests::test_turn_with_quiet_stdout_but_active_subagent_is_not_killed
    ```
    This is the bug reproduced end-to-end through the real driver: a turn doing real subagent work is killed.

    PASSES AFTER THE FIX (mutation reverted, file restored from backup):
    ```
    tests/test_stall_progress_integration.py::SubagentProgressSurvivalTests::test_observer_is_wired_with_the_log_from_xdg_data_home PASSED [  3%]
    tests/test_stall_progress_integration.py::SubagentProgressSurvivalTests::test_turn_with_quiet_stdout_but_active_subagent_is_not_killed PASSED [  6%]
    tests/test_stall_progress_integration.py::TrueHangPreservationTests::test_noisy_hang_kill_is_not_achieved_by_ignoring_the_log PASSED [ 10%]
    tests/test_stall_progress_integration.py::TrueHangPreservationTests::test_noisy_permission_deadlock_is_still_killed PASSED [ 13%]
    tests/test_stall_progress_integration.py::TrueHangPreservationTests::test_silent_hang_is_still_killed PASSED [ 16%]
    tests/test_stall_progress_integration.py::WatchdogRemainingTests::test_agy_watchdog_has_the_same_accessor PASSED [ 20%]
    tests/test_stall_progress_integration.py::WatchdogRemainingTests::test_remaining_counts_down_from_the_timeout PASSED [ 23%]
    tests/test_stall_progress_integration.py::WatchdogRemainingTests::test_remaining_is_none_when_disabled PASSED [ 26%]
    tests/test_stall_progress_integration.py::WatchdogRemainingTests::test_remaining_never_negative PASSED [ 30%]
    tests/test_stall_progress_integration.py::WatchdogRemainingTests::test_touch_resets_remaining PASSED [ 33%]
    ```
    The passing assertion is both `ipd-stalled == []` AND `item["status"] == "executed"` with driver exit 0, so
    the turn was not merely un-killed, it completed.

    PROGRESS SOURCE: recorded on the display and asserted in
    `tests/test_stall_countdown_display.py::StatuslineCountdownTests::test_progress_source_is_named_on_the_statusline`
    (`subagent` and `stdout` both PASSED, see V-04). In the driver, a stdout line calls
    `statusline.touch("stdout")` (oc_runipd.py, turn loop) and observed subagent progress calls
    `statusline.touch("subagent")` via `_subagent_progress`.

    THREAD HYGIENE (`threading.enumerate()` compared before/after the scope, pasted above as part of the
    stall_progress run): `PollerThreadHygieneTests::test_thread_does_not_outlive_the_context PASSED` asserts the
    named `aw-subagent-progress` thread is present DURING the scope and absent after, and
    `test_repeated_attempts_do_not_accumulate_threads PASSED` runs four sequential attempts and asserts zero
    surviving observer threads, so the poller cannot leak across retries. The poller shares the turn's
    `with statusline, watchdog, poller:` scope, which is what makes this structural rather than incidental.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted test output asserting the heartbeat line contains BOTH the time since last observed progress AND the remaining time before the stall kill, and names the progress source. Assert the countdown DECREASES across two successive renders with a fixed/injected clock (e.g. "stall kill in 2m30s" then "... 2m15s"), so it is a real countdown and not static text. Assert the countdown agrees with the WATCHDOG's remaining time (drive the watchdog's clock, not the heartbeat's, and show the line follows it) - a display computing its own independent countdown fails this item. Assert that with the watchdog disabled (`stall_timeout=0`) the line omits any countdown claim. Assert the phrase "still working" with no countdown no longer appears.
  - Observed evidence: SCOPE NOTE FIRST (recorded as DECISION 06-kaga7s-D1 in the run register): this plan was
    authored/reviewed hours BEFORE commit `b62e7634` ("feat(runner): add live sticky statusline", 2026-08-29
    22:22) replaced `Heartbeat` with `Statusline` as the live quiet-turn display in BOTH drivers.
    `grep -rn "Heartbeat(" agent_workflows/` now returns NOTHING (zero production instantiations). Implementing
    E-04 only on `Heartbeat` would have shipped an honest countdown in a class no operator sees, missing the
    plan's stated GOAL. So the countdown was added to BOTH the LIVE display (`Statusline`) and `Heartbeat`, both
    reading ONE authority: the new `StallWatchdog.remaining()`.

    `python3 -m pytest tests/test_stall_countdown_display.py -p no:randomly -v -o addopts=""`:
    ```
    tests/test_stall_countdown_display.py::CountdownFormatterTests::test_disabled_watchdog_claims_no_countdown PASSED [ 36%]
    tests/test_stall_countdown_display.py::CountdownFormatterTests::test_formats_bare_seconds_under_a_minute PASSED [ 40%]
    tests/test_stall_countdown_display.py::CountdownFormatterTests::test_formats_minutes_and_seconds PASSED [ 43%]
    tests/test_stall_countdown_display.py::CountdownFormatterTests::test_names_the_progress_source PASSED [ 46%]
    tests/test_stall_countdown_display.py::CountdownFormatterTests::test_never_renders_a_negative_countdown PASSED [ 50%]
    tests/test_stall_countdown_display.py::StatuslineCountdownTests::test_a_broken_watchdog_degrades_silently PASSED [ 53%]
    tests/test_stall_countdown_display.py::StatuslineCountdownTests::test_countdown_appears_on_the_live_statusline PASSED [ 56%]
    tests/test_stall_countdown_display.py::StatuslineCountdownTests::test_countdown_decreases_across_successive_renders PASSED [ 60%]
    tests/test_stall_countdown_display.py::StatuslineCountdownTests::test_countdown_follows_the_watchdogs_clock_not_its_own PASSED [ 63%]
    tests/test_stall_countdown_display.py::StatuslineCountdownTests::test_layout_invariant_holds_with_the_countdown PASSED [ 66%]
    tests/test_stall_countdown_display.py::StatuslineCountdownTests::test_layout_is_unchanged_when_no_countdown PASSED [ 70%]
    tests/test_stall_countdown_display.py::StatuslineCountdownTests::test_no_countdown_when_no_watchdog_supplied PASSED [ 73%]
    tests/test_stall_countdown_display.py::StatuslineCountdownTests::test_no_countdown_when_watchdog_disabled PASSED [ 76%]
    tests/test_stall_countdown_display.py::StatuslineCountdownTests::test_progress_source_is_named_on_the_statusline PASSED [ 80%]
    tests/test_stall_countdown_display.py::HeartbeatCountdownTests::test_bare_still_working_wording_is_gone PASSED [ 83%]
    tests/test_stall_countdown_display.py::HeartbeatCountdownTests::test_countdown_follows_the_watchdog PASSED [ 86%]
    tests/test_stall_countdown_display.py::HeartbeatCountdownTests::test_message_names_the_progress_source PASSED [ 90%]
    tests/test_stall_countdown_display.py::HeartbeatCountdownTests::test_message_states_the_countdown PASSED [ 93%]
    tests/test_stall_countdown_display.py::HeartbeatCountdownTests::test_no_countdown_when_disabled PASSED [ 96%]
    tests/test_stall_countdown_display.py::HeartbeatCountdownTests::test_no_driver_source_contains_the_misleading_phrase PASSED [100%]
    ============================== 30 passed in 4.69s ==============================
    ```
    Mapping to each required assertion:
    - BOTH time-since-progress AND time-to-kill: `test_message_states_the_countdown` asserts `no progress` and
      `kill in 2m30s` in one line; the rendered live line is e.g.
      `0m00s idle: 0s kill in 45s` (captured verbatim from a failing-assertion diff during development).
    - DECREASES across successive renders with an injected clock:
      `test_countdown_decreases_across_successive_renders` drives 90/75/60/45s and asserts
      `kill in 1m30s` -> `kill in 1m15s` -> `kill in 1m00s` -> `kill in 45s`.
    - AGREES WITH THE WATCHDOG (the anti-independent-clock assertion):
      `test_countdown_follows_the_watchdogs_clock_not_its_own` moves ONLY the watchdog's `remaining()` and asserts
      the line follows it (`2m30s` -> `2m15s`, and asserts the stale value is GONE) while never touching the
      display's own `_last_activity`. A display computing its own countdown fails this test.
      `WatchdogRemainingTests` (V-03 paste) separately proves `remaining()` really counts down, resets on
      `touch()`, and never goes negative.
    - WATCHDOG DISABLED omits the claim: `test_no_countdown_when_watchdog_disabled` and
      `CountdownFormatterTests::test_disabled_watchdog_claims_no_countdown` (`--stall-timeout 0` ->
      `remaining()` is None -> `format_stall_countdown(None) == ""`). Also `test_no_countdown_when_no_watchdog_supplied`.
    - "still working" GONE: `test_bare_still_working_wording_is_gone` plus
      `test_no_driver_source_contains_the_misleading_phrase`, which greps EVERY module in the package and asserts
      no file contains `still working on`, so the phrasing cannot return via a copy.
    - Progress source named: `test_progress_source_is_named_on_the_statusline` (`subagent` and `stdout`).
    - ADDITIVE, not a silent reformat: `test_layout_is_unchanged_when_no_countdown` asserts the pinned golden
      column still renders exactly `64m21s idle: 14s` with no countdown, and
      `test_layout_invariant_holds_with_the_countdown` asserts `len(l1) == len(l2)` still holds WITH it. The
      pre-existing pinned layout test `tests/test_render_stream.py::StatuslineUnitTests` remains green.
    - Best-effort display: `test_a_broken_watchdog_degrades_silently` (a `remaining()` that raises yields no
      countdown rather than breaking the line).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted `grep -c "class Heartbeat:" agent_workflows/agy_runipd.py agent_workflows/render_stream.py` showing `0` for agy and `1` for render_stream, plus a pasted grep showing agy imports it from `agent_workflows.render_stream`. Plus the extended single-definition test from `tests/test_render_stream.py` passing (pasted), asserting `agy_runipd.Heartbeat is render_stream.Heartbeat`. Plus pasted evidence that agy's stall wiring is unchanged (the agy runner suite green).
  - Observed evidence: `grep -c "class Heartbeat:" agent_workflows/agy_runipd.py agent_workflows/render_stream.py`:
    ```
    agent_workflows/agy_runipd.py:0
    agent_workflows/render_stream.py:1
    ```
    `grep -n "render_stream import" agent_workflows/agy_runipd.py`:
    ```
    44:from agent_workflows.render_stream import Heartbeat as Heartbeat
    45:from agent_workflows.render_stream import Statusline
    ```
    (The `as Heartbeat` alias is deliberate: `Heartbeat` is not referenced elsewhere in `agy_runipd`, and the
    repo's `ruff` pre-commit hook auto-STRIPPED a bare import as unused on the first attempt, which broke
    `tests/test_agy_runipd_shim.py`'s object-identity re-export assertion. The explicit re-export alias keeps the
    public surface intact without a partial `__all__` that would understate the module's other public names.)

    Object identity in both drivers:
    ```
    agy_runipd.Heartbeat is render_stream.Heartbeat: True
    oc_runipd.Heartbeat  is render_stream.Heartbeat: True
    ```
    Extended single-definition tests (`tests/test_render_stream.py`), including the NEW agy coverage the plan
    asked for (previously only oc was guarded):
    ```
    tests/test_render_stream.py::SingleDefinitionTests::test_agy_runipd_has_no_inline_heartbeat_copy PASSED [ 83%]
    tests/test_render_stream.py::SingleDefinitionTests::test_definitions_live_in_render_stream_module PASSED [ 87%]
    tests/test_render_stream.py::SingleDefinitionTests::test_exactly_one_heartbeat_definition_in_the_package PASSED [ 90%]
    tests/test_render_stream.py::SingleDefinitionTests::test_heartbeat_is_the_same_object_in_both_drivers PASSED [ 93%]
    tests/test_render_stream.py::SingleDefinitionTests::test_names_are_the_same_objects PASSED [ 96%]
    tests/test_render_stream.py::SingleDefinitionTests::test_oc_runipd_source_has_no_inline_definitions PASSED [100%]
    ============================== 31 passed in 0.36s ==============================
    ```
    `test_exactly_one_heartbeat_definition_in_the_package` globs EVERY module in the package and asserts the only
    definer is `render_stream.py`, so the duplicate cannot silently return in a third module either.

    AGY STALL WIRING UNCHANGED: agy received the DISPLAY change only (`statusline.watchdog = watchdog` plus a
    `remaining()` accessor for parity); it got NO progress observer, because its stdout already carries
    `step_type == "subagent"` events (agy_runipd.py `render_agy_event`) and every stdout line already touches the
    watchdog. Agy runner suites green:
    ```
    python3 -m pytest tests/test_agy_runipd_cli.py tests/test_agy_runipd_shim.py tests/test_session_rotation.py -q
    ..........................                                               [100%]
    (26 passed)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: THE TRUE-HANG PRESERVATION TESTS, pasted, in BOTH variants, because the observer's whole risk is defeating them. (a) SILENT HANG: no stdout and no log activity at all -> the watchdog still fires at the timeout and `ipd-stalled` is recorded. (b) NOISY HANG (the realistic permission deadlock per backlog `qyaime`): no stdout, no agent-loop progress, but background log lines for our own process continuing to arrive (`message=evaluated permission=external_directory ...`, `message="llm runtime selected"`) -> the watchdog STILL fires and `ipd-stalled` is STILL recorded. Variant (b) is the load-bearing one: if it passes only because the observer ignores the log entirely, or fails because noise resets the clock, the fix is wrong. Neither variant may be made to pass by lengthening or disabling the timeout. Finally paste a full default-suite run `python3 -m pytest -p no:randomly` summary line showing green.
  - Observed evidence: BOTH variants are first-class tests in
    `tests/test_stall_progress_integration.py::TrueHangPreservationTests`, both launching the REAL driver and both
    asserting the same three things: queue item `interrupted`, attempt `interrupt_reason == "stall_timeout"`, and
    an `ipd-stalled` event actually recorded in `events.jsonl` (plus driver exit 1).
    ```
    tests/test_stall_progress_integration.py::TrueHangPreservationTests::test_noisy_hang_kill_is_not_achieved_by_ignoring_the_log PASSED [ 10%]
    tests/test_stall_progress_integration.py::TrueHangPreservationTests::test_noisy_permission_deadlock_is_still_killed PASSED [ 13%]
    tests/test_stall_progress_integration.py::TrueHangPreservationTests::test_silent_hang_is_still_killed PASSED [ 16%]
    ```
    (a) SILENT HANG (`test_silent_hang_is_still_killed`): child is `time.sleep(60)`, the log file exists but never
    receives a line. Killed at `--stall-timeout 0.4`.

    (b) NOISY HANG (`test_noisy_permission_deadlock_is_still_killed`), the load-bearing one, modeled directly on
    backlog `qyaime`: the child emits NO stdout and NO agent-loop progress, but announces a child session and then
    continuously writes the exact chatter a permission-deadlocked opencode produces
    (`message=asking ... permission=external_directory patterns=[...]`, `message=evaluated permission=bash`,
    `message="llm runtime selected"`, `message=tracking`, `message="resolved path"`) every 50ms for the whole
    window. STILL killed at `--stall-timeout 0.5`. Neither variant was made to pass by lengthening or disabling
    the timeout: both use a SHORT, explicitly non-zero timeout and both assert the kill actually happened.

    PASSES FOR THE RIGHT REASON (the trap the plan warned about): variant (b) would be worthless if it passed
    merely because the observer was inert. `test_noisy_hang_kill_is_not_achieved_by_ignoring_the_log` proves the
    observer WAS reading that log and still correctly reported no progress:
    it asserts (1) `poll()` is False on the noise, (2) the child WAS learned from the log
    (`_CHILD in obs.known_children()`, i.e. the log really was parsed), (3) `progress_count == 0` after 150
    housekeeping lines, and (4) a single genuine `message=loop` line DOES flip `poll()` to True, proving the
    observer is live rather than disabled. This is the assertion that separates "correct attribution" from
    "observer switched off".

    WHY THIS GUARANTEE IS LOAD-BEARING: the classification is a CLOSED allowlist
    (`PROGRESS_MESSAGE_KINDS = {loop, process, stream}`, asserted by
    `ProgressClassificationTests::test_progress_kinds_are_a_closed_allowlist`), so a future opencode housekeeping
    kind cannot silently start counting as progress and make a deadlocked run immortal. The rationale is
    documented next to the code so a later "simplify to any log line" change cannot destroy it unknowingly.

    FULL DEFAULT SUITE, `python3 -m pytest -p no:randomly`:
    ```
    ........................................................................ [ 98%]
    ....................................                                     [100%]
    2985 passed, 3 skipped, 4 xfailed in 59.24s
    ```
    ZERO failures. Worth noting for the morning reviewer: three earlier turns in this run reported 15
    pre-existing `tests/test_run_viewer.py` failures (ambient-state dependence on the live `.aw/records/runs/`
    tree); in THIS worktree that file is green, so no failure is being excused or inherited here.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make the stall decision progress-aware and the display honest); E-items are ordered sub-steps (establish attribution -> observer -> oc wiring -> honest display -> single Heartbeat so the display reaches both drivers).

Execution contract:

1. Open questions: OQ-01 and OQ-02 both resolved (OQ-02 in review, from live evidence: the two-hop parent-session attribution route plus the loop/process/stream progress classification). E-01 is retained as a CONFIRMATION step against the running opencode, not an open design decision; if that confirmation fails, STOP and report a REPLAN - do not proceed to E-02 with an approximate key. Execution requires explicit human approval.
2. Scope fence: touch ONLY `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py` (E-05's Heartbeat import ONLY), `agent_workflows/render_stream.py`, and `tests/` (plus the one new observer module and its fixture). Do NOT change `DEFAULT_STALL_TIMEOUT`, do NOT alter the kill path, do NOT add a progress observer to the agy driver, do NOT extract a shared runner library (backlog `dhuape`), and do NOT attempt to fix the upstream opencode permission hang (backlog `qyaime`). If the work seems to need more, STOP and report.
3. Honesty rule (HARD MUST): every V-item's Observed evidence is the ACTUAL pasted output of the named command. A V-item whose test was not run stays `Result: pending`. Additionally, do NOT restate this plan's incident evidence as proven beyond what the Findings say: the subagent blind spot is reproduced, but the four recorded 2026-08-29 kills are NOT established as instances of it, and the fix must not be reported as having fixed them.
4. Fail-safe rule: the log observer is BEST-EFFORT. It must never raise into the turn, never block, and never become a hard dependency; if it cannot read or parse, behavior degrades to today's stdout-only watchdog. A missing log must not turn into a hung or crashed run.
5. Do-not-weaken rule (the highest-risk rule in this plan): the true-hang kill MUST survive BOTH the silent and the NOISY hang (V-06). Counting any log line for our process as progress would make a permission-deadlocked run immortal - strictly worse than today's bug, because a killed turn is recoverable and an immortal one is not. If a change makes V-06 pass only by lengthening or disabling the timeout, or by ignoring the log entirely, that is a failure. The guarantee is "no genuine agent-loop progress from any source for the timeout => killed".
6. Privacy rule: no real opencode session id (`ses_...`) may enter a committed fixture, test, or user-visible line; the leak sanitizer flags it (leak_sanitizer.py:81). Run `aw sanitize --agent` before committing fixtures.
7. Commit ONLY this plan's own changed files, path-scoped; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
8. Lifecycle move on completion: verify all V items with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`.
