---
id: 7so8uz
created: 20261001
set: 4xtpvg
order: 00
topic: [turn-bounds, lane-containment, permission-deadlock]
model: 
kind: assessment
status: active
outcome: answered
summary: Measured: an opencode permission ask never reaches the driver's stdout stream, so A10c option (i) is unsatisfiable there; the log is the only carrier and the 2026-09-05 deny posture already closed the isolated-turn case
consumed-by: [0b7fic]
priority: medium
---

# Can the driver observe an opencode permission ask, and is a PERMISSION_TIMEOUT worth arming?

Measured 2026-10-01 in lane `4xtpvg` at HEAD `ce55ef615`, for backlog item `4xtpvg` (the permission
bound has no production trigger). Every number below came from running a query over real recorded
artifacts, never from reading code and inferring. The two corpora are:

- **the host log**, `$XDG_DATA_HOME/opencode/log/opencode.log`, 2,493,369 lines spanning
  2026-07-08T03:22:40Z to 2026-10-01T23:41:12Z;
- **the driver's own recorded child stdout**, `.aw/records/runs/*/sessions/*.jsonl`, 2,414 files,
  788,504 JSON events, 1.28 GB, which is the EXACT byte stream `oc_runipd.run_opencode` iterates in
  `for line in process.stdout`.

The second corpus is what makes this assessment different from every prior attempt at this question.
Spec `7ckptx` A10c demands a captured stream from a real provoked ask. The driver has been capturing
that stream, per attempt, for months; nobody had queried it.

## Answer, in one line

**Detection on stdout is IMPOSSIBLE, not merely unproven.** A permission ask is a host-internal event
that never appears in the `--format json` stdout stream at all, so spec `7ckptx` A10c option (i) is
unsatisfiable as written, and option (ii) is the correct and honest route. Separately, and more
consequentially, the ask the bound was designed for **has not occurred on a driver turn since
2026-09-13** because the R4.1 deny posture removed its cause.

## Finding 1. The stdout stream carries SIX event types and none of them is a permission

Over all 788,504 recorded stdout events the complete type census is:

```
(step_update, carried as {"event":...} with no "type" key)   273,961
tool_use                                                     148,886
step_start                                                   135,208
step_finish                                                   135,049
text                                                           94,623
error                                                              10
```

Events whose `type` mentions `permission`, `ask`, or `question`: **0**. The 5,775 stdout lines whose
RAW TEXT contains the substring `permission` are all `tool_use` payloads, i.e. a tool call whose own
arguments happen to mention the word (a `bash` command string, a `read` file path); none is a
permission event.

CONSEQUENCE FOR THE SPEC. R4.4b says the detector "may be matching a shape that never reaches the
stream it inspects", and hedges. It does not reach it. A10c option (i) asks the implementing plan to
"provoke a real permission ask, capture the stream, and paste the matched line"; there is no line to
match, and 1,166 real asks (Finding 2) produced 1,166 absences. A10c's own prohibition on a synthetic
line is therefore not a bar an implementer can clear by trying harder.

## Finding 2. Asks ARE recorded, in the log, and are attributable to a driver turn

The log carries the ask on one line shape (REDACTED: the real line carries a machine-local absolute
path and a real request handle, both of which the leak sanitizer refuses in tracked text, so the
identifier and the home-rooted pattern are replaced by placeholders here):

```
timestamp=2026-09-13T16:03:58.088Z level=INFO run=1b919db7 message=asking \
  id=per_<redacted> permission=external_directory patterns="[\"/tmp/opencode/*\",\"<HOME>/VC/*\"]"
```

The shape that matters is the three fields a detector would key on: `message=asking`, a
`permission=<class>` naming the permission class, and the `run=` token that makes the line
attributable. The pattern list's CONTENTS are incidental to detection and are exactly the part that
cannot be quoted verbatim in a tracked artifact.

Census over the whole log: **1,552** `message=asking` lines carrying `permission=`, plus 2,245
carrying `questions=<N>` (the interactive-question class). Of the permission asks, **1,166** are
attributable to a driver turn, by resolving the line's `run=` token to an `aw-*`-titled root session
(`message=created ... parentID=undefined title=aw-exec-run-...`).

ATTRIBUTION IS SOUND AND AVAILABLE IN TIME, which matters because a detector must know an ask is
*ours* before acting on it:

- 917 `aw-*` root sessions exist; **917 of 918** resolve to at least one `run=` token.
- For **1,219 of 1,552** asks the ask's `run=` token was ALREADY bound to an `aw-*` root session
  EARLIER in the log, so the binding is learnable before the ask rather than after.
- Ambiguity is **0**: no ask's `run=` token was bound to more than one `aw-*` root session at ask
  time, and no session id maps to more than one run token.
- The remaining 333 asks belong to run tokens with no `aw-*` root session, i.e. a human TUI session,
  correctly NOT ours.

The driver can also reach this from the other direction with the hop `stall_progress` already owns:
of 1,559 recorded stdout streams, **1,558** have a first `sessionID` that resolves to an `aw-*` root
`created` line in the log. So a live observer has two independent routes to decide "this ask is mine",
and the existing module already implements the harder of the two.

## Finding 3. The false-positive bill at the specified 30 seconds is 15 healthy turns killed

This is the measurement that decides whether arming is safe, and R4.4b names exactly this risk ("a
false positive kills a healthy turn"). For each of the 1,166 driver-turn asks, joined to the recorded
stdout stream of its own root session, the gap from the ask to the NEXT stdout event is what
`note_progress()` would use to disarm the bound:

```
n=1149   min=0.001s   p50=0.025s   p90=0.351s   p95=2.512s   p99=40.106s   max=163.5s
```

A window of W seconds would have fired on a turn that went on to produce stdout:

```
W=  10s ->  20 of 1149  (1.74%)
W=  30s ->  15 of 1149  (1.31%)     <-- the spec's R4.4(a) default
W=  60s ->   7 of 1149  (0.61%)
W= 120s ->   4 of 1149  (0.35%)
W= 300s ->   0 of 1149  (0.00%)
W= 600s ->   0 of 1149  (0.00%)
```

So the spec's own normative 30-second default would have killed **15 healthy turns** in this corpus.
A naive reading says "use 300s then", and that is where Finding 4 refuses.

## Finding 4. The value side is ZERO on this corpus: every genuinely silent ask is already covered

Of the 1,166 asks, **17** were followed by no further stdout event ever, which is the only shape a
permission bound could usefully kill. For all 17, the question is whether the EXISTING
`StallWatchdog` already covers them, since it is advanced by stdout lines and, since `kaga7s`, also
by `stall_progress.SubagentProgressObserver` reporting subagent log progress.

Measured per ask, counting only the log progress kinds the observer actually counts
(`PROGRESS_MESSAGE_KINDS` = `loop`/`process`/`stream`) and only on sessions whose `parentID` chains to
that turn's root:

```
asks with NO later stdout event:                                        17
  of those, with later SUBAGENT progress (watchdog reset, would NOT fire):  0
  of those, with NO subagent progress (watchdog DOES fire and kill):       17
```

All 17 are covered by the shipped stall watchdog, whose default is `DEFAULT_STALL_TIMEOUT = 900.0`.
Nothing in this corpus is a case a permission bound would catch and the stall watchdog would miss.

This refutes a plausible worry worth stating because it was checked rather than assumed: a
permission-deadlocked child keeps emitting housekeeping log lines (`stall_progress`'s docstring
measures `evaluated` 4174, `tracking` 2567, `asking` 97 in one 3MB slice), so one might expect the log
observer to mask a deadlock and defeat the watchdog. It does not, because the observer counts a CLOSED
ALLOWLIST of agent-loop kinds and excludes every housekeeping kind by design. The design note is not
only correct in principle, it is correct on every one of the 17 real cases.

## Finding 5. The cause was removed in product, and the asks STOPPED

Driver-turn permission asks per day, split by whether the opencode instance directory was a lane
worktree (i.e. an isolated turn):

```
                                turns  | ISOLATED turns asked asks | NON-ISOLATED turns asked asks
all time                          917  |     768        80  1121   |     149        11    45
on/before 2026-09-05              179  |      92        76  1102   |      87         5    21
after 2026-09-05 (deny landed)    738  |     676         4    19   |      62         6    24
after 2026-09-13 (last ask)       640  |     635         0     0   |       5         0     0
```

Commit `8a491d4c1` (2026-09-05, `lanectn` Order 03 `lhmrhx`) landed BOTH the R4.1 deny posture
(`permission.external_directory=deny`, `permission.question=deny` via `OPENCODE_CONFIG_CONTENT`, which
makes the host REFUSE instead of ASK) and `note_permission_request` itself. The asks fall off a cliff
immediately after it: 1,102 isolated-turn asks before, 19 after, and **0 across 640 driver turns since
2026-09-13**, over a period with heavy continuous driver use (89 turns on 2026-10-01 alone).

The four residual isolated turns that asked are all dated 2026-09-06, all from the single run
`run-20260905T211011Z-3780617` that was executing the `lanectn` Set itself, i.e. turns whose own lanes
predated the landing.

So the deadlock class was closed ARCHITECTURALLY, by denial, which is the stronger fix and the one
backlog `qyaime` itself prescribed ("the fix is NOT to grant the agent access to the main repo ... it
is to stop the driver from pointing the agent at main-repo paths"). The bound was the backstop for a
hole that the same commit filled.

## What follows for the product, stated as a recommendation and not a decision

1. **Do NOT arm `PERMISSION_TIMEOUT` and do NOT wire a stdout detector.** Both are refused by
   measurement: the stream carries no such event (F1), the specified default costs 15 false kills
   (F3), and the benefit is zero because the stall watchdog already covers all 17 candidate cases
   (F4).
2. **Amend spec `7ckptx` R4.4b and A10c** to record that option (i) is UNSATISFIABLE on stdout rather
   than merely unattempted, and that option (ii) is therefore taken permanently rather than
   provisionally. The spec currently offers a choice whose first branch cannot be walked.
3. **Keep the mechanism, or delete it, as a maintainer call.** `TurnBoundWatch` already implements
   the resettable permission bound correctly; it costs nothing while `PERMISSION_TIMEOUT` is `0.0`,
   and a future host whose stream DOES carry permission events could arm it without redesign. The
   opposite reading (GUIDING_PRINCIPLES P6, no mechanism for a hypothetical need) is equally
   defensible. What is NOT defensible is leaving the current state undocumented, where a reader finds
   a method with no caller and cannot tell whether that is a bug or a decision.
4. **Residual exposure, named so it is not lost.** The deny posture is applied to ISOLATED turns only
   (`oc_runipd.run_opencode` applies it inside `if work_dir:`), so a NON-isolated unattended turn still
   gets no denial and relies on `--auto` plus the stall watchdog. 24 of the 45 non-isolated asks in
   this corpus postdate the deny posture for exactly that reason. This is consistent with R4.1, which
   scopes the posture to isolated turns deliberately, and it is the one place a future permission
   deadlock could still arise.

## Reproduction

The five queries are small, pure, read-only Python over the two corpora described above; each is
restated in the plan this assessment feeds (`consumed-by:` above, plan `0b7fic` E-01) so an executor re-derives the
numbers rather than trusting them. They need no fixture and no network: the log path comes from
`stall_progress.default_log_path()` and the stream corpus from `.aw/records/runs/*/sessions/*.jsonl`.
Both are MACHINE-LOCAL and uncommitted, so the numbers are reproducible on this machine and must be
re-measured rather than assumed on another.
