- Id: wjl471
- Status: open
- Set: commitguard
- Priority: high
- Work-Kind: feature
- Summary: Commit guard that detects agent context from the environment and redirects to the tooled path: an accident-stopper, not a security boundary, plus wire the four existing gates that are currently invoked by nothing

## Workflow history
- 2026-08-31 created (aw backlog): Commit guard that detects agent context from the environment and redirects to the tooled path: an accident-stopper, not a security boundary, plus wire the four existing gates that are currently invoked by nothing

GOAL: a commit guard that catches the ACCIDENT, tells the agent what to do instead, and is cheap
enough to always be on. NOT a security boundary. The distinction is deliberate and is the whole
design premise, so it is stated first.

THE THREAT MODEL, decided by the maintainer 2026-08-31 and supported by measured evidence.

Agents do not go rogue here; they act on TRAINED REFLEX. They are trained to run SOLO in repos they
fully control, where `git add -A` is correct and expected. This repo asks for something that is, for
lack of a better term, not in their nature. Every failure observed in the 2026-08-31 session fits that
shape, and NONE required an agent to defy an instruction it had understood:

| Failure | Cause | Needed malice? |
| --- | --- | --- |
| An agent committed 18 files into `main` while its lane branch stayed at ZERO commits | The prompt said "leave the main execution checkout safe" AND every absolute path in that same prompt was main's; the agent read `../../../DECISIONS.md` because the prompt handed it that path | No |
| `codex` re-authored plan `ntf6sx` into `pending/` 3.5 hours AFTER its twin finalized to `executed/` (20:04:27 -> 23:27:42) | Nothing signalled that the work had already landed | No |
| A walkthrough claimed its plan's `id6` as its own identity, breaching D140 | Reflex to make the plan/walkthrough pairing greppable by sharing an id | No |
| 21 plans stranded in lanes, 24 hand-merges, roughly $528 | Two independently sensible defaults that silently cancelled each other | No |

CONSEQUENCE FOR THE DESIGN. A guard that REFUSES and says "we want you to use X instead" would very
likely have caught all four. BYPASSABILITY IS A FEATURE, NOT A WEAKNESS, against accidents: the
operator must be able to override deliberately when they mean to. Do NOT reject a design merely
because `--no-verify` defeats it; that objection applies a security standard to a safety problem.

THE ONE CAVEAT THAT STILL MATTERS: a bypassable guard must never be DESCRIBED as a boundary, because
that is how a fail-open check comes to be trusted. The shipped `prepush-authorization-gate` already
gets this right, printing its own limit out loud: "this is a LOCAL, OPT-IN, bypassable (`--no-verify`)
FEEDBACK hook, NOT an authority boundary and NOT independent authorization - a local env ack is
settable by the agent." Reuse that honesty pattern verbatim.

FINDING 1: AGENT CONTEXT IS RELIABLY DETECTABLE FROM THE ENVIRONMENT. Measured across FIVE agent
hosts plus a plain login shell, with the raw dumps committed as evidence in `tmp/` (see EVIDENCE
below). Every host self-identifies, and NO marker appears in the plain shell, so a detector keyed on
these has no false positives on a human at a terminal:

| Host | Markers observed |
| --- | --- |
| OpenCode | `AGENT=1`, `OPENCODE=1`, `OPENCODE_PID=<pid>` |
| Antigravity | `AI_AGENT=antigravity`, `ANTIGRAVITY_AGENT=1`, plus `ANTIGRAVITY_CONVERSATION_ID` / `ANTIGRAVITY_TRAJECTORY_ID` / `ANTIGRAVITY_PROJECT_ID` |
| Codex | `CODEX_SESSION_ID`, `CODEX_THREAD_ID`, `CODEX_PERMISSION_PROFILE`, `CODEX_SANDBOX_NETWORK_DISABLED` |
| Hermes | `HERMES_SESSION_ID`, `HERMES_INTERACTIVE`, `HERMES_QUIET`, `HERMES_REAL_HOME` |
| Claude Code | `AI_AGENT=claude-code_2-1-252_agent`, `CLAUDECODE=1`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_PID`, `CLAUDE_CODE_ENTRYPOINT` |
| plain login shell | NONE of the above |

TWO OBSERVATIONS THAT SHOULD SHAPE THE IMPLEMENTATION.

(a) `AI_AGENT` IS THE SHAPE TO STANDARDIZE ON. Two of the five hosts (Antigravity and Claude Code)
    ALREADY set it, and it is the only marker that is both host-neutral in NAME and carries WHICH
    agent as its VALUE. A guard keyed on a generic `AI_AGENT` plus a fallback list of vendor-specific
    markers does not need a code change every time a new host appears; an unknown future host can
    self-declare. Consider also SETTING `AI_AGENT` ourselves in the drivers for hosts that do not,
    so downstream tooling has one thing to read.

(b) EVERY HOST LEAKS A SESSION OR THREAD ID, which is a STRONGER signal than a bare boolean flag: a
    plain shell has no reason to set one, whereas a boolean like `AGENT=1` is the sort of thing a
    user might set for unrelated reasons. Prefer the id-bearing markers when deciding, and record the
    id in the refusal message so an accident is traceable to a specific session.

FINDING 2: FOUR OF THE SIX EXISTING GATES ARE WIRED TO NOTHING, which is very likely a bigger
real-world win than any new guard, and is nearly free because the code already exists and works.
MEASURED at HEAD `187318eb`:

| Gate (exists as a working `aw` verb) | In `.pre-commit-config.yaml`? | In `Makefile`? |
| --- | --- | --- |
| `ipd-executed-gate` | YES | no |
| `ipd-status-untooled-gate` | YES | no |
| `precommit-scope-gate` | **no** | no |
| `prepush-authorization-gate` | **no** | no |
| `backlog-blocking-close-gate` | **no** | no (documented as deliberately opt-in) |
| `ipd-dependency-statement-gate` | **no** | no |

Also measured: the ONLY installed git hook is `pre-commit`. There is NO `pre-push` hook, so
`prepush-authorization-gate` CANNOT fire even though running it by hand prints a correct, actionable
refusal. A guard that is never invoked is not a guard.

WHAT TO SOLVE FOR, not prescribed here.

1. WHERE DOES THE GUARD LIVE? A `pre-commit` hook sees the staged set but not the INTENT (it cannot
   tell `git add -A` from an explicit path list, because staging already happened). A wrapper around
   `git` would see intent but is invasive and easy to bypass by calling `/usr/bin/git` directly.
   Reading `git reflog`/`ORIG_HEAD` after the fact catches it too late. Decide deliberately, and note
   the shipped `git_commit_helper.offer_commit` already enforces the desired behavior for callers
   that USE it, so part of the answer may be "make the tooled path the path of least resistance"
   rather than intercepting the untooled one.
2. WHAT EXACTLY IS THE ACCIDENT TO CATCH? Candidates, all observed: staging paths the agent did not
   modify (the `add -A` reflex); committing in the MAIN checkout while an isolated lane was allocated
   for the turn (the 18-file case, which is the most expensive one and is detectable, because the
   driver knows the lane path); using `--no-verify` without a stated reason; pushing at all.
3. HOW DOES IT TELL THE AGENT WHAT TO DO? The refusal message IS the product here, not a side effect.
   It must name the exact replacement command (e.g. `aw commit <plan> -- <paths>`), state that the
   refusal is a local accident-guard and not an authority boundary, and say how to override
   deliberately. Copy the tone of `prepush-authorization-gate`'s existing message.
4. HOW IS IT OVERRIDDEN, AND IS THAT AUDITABLE? An env-var acknowledgement is settable by the agent
   itself, which is fine for accidents but means the override should be RECORDED (which agent, which
   session id, which reason) rather than silently honored.
5. SHOULD THE FOUR UNWIRED GATES SIMPLY BE INSTALLED FIRST? They may catch most of the remaining
   accidents at near-zero cost. Note `backlog-blocking-close-gate` is documented as deliberately
   opt-in, so confirm each gate's intent before wiring it; do not assume "unwired" means "forgotten".

EVIDENCE, committed with this item so a successor does not have to re-capture five hosts:
`tmp/env-from-opencode.txt`, `tmp/env-from-agy.txt`, `tmp/env-from-codex.txt`,
`tmp/env-from-hermes.txt`, `tmp/env-from-claude.txt`, `tmp/env-straight-from-command-line.txt`.
NOTE: `tmp/` is GITIGNORED, so these dumps are LOCAL ONLY and will not survive a fresh clone. If the
detection matrix is to be relied on later, the marker table above (which is committed with this item)
is the durable record; re-capture the dumps if raw environments are needed again. Also note the dumps
contain machine-local paths and session ids, so they should NOT be committed as-is without running
`aw sanitize`.

RELATED. `mjx7ne` (hostcap-01) describes host capabilities including `commit_gateway` and `deny_push`,
both of which grep to ZERO enforcement today; under this item's threat model those are worth shipping
as honestly-labelled ACCIDENT GUARDS rather than being narrowed away. `suugsf` covers the contract
never warning that other agents share the checkout. `a8eufb` and `077yqc` cover finalize
misattributing a concurrent agent's files. The cross-platform confinement research prompt
(`q65sz3`) covers the harder OS-level question, which this item deliberately does NOT depend on.
