# IPD: Portable inter-agent comms convention (.agents/comms/ + envelope + Not-Before + ack format + installer scaffold)

- Date: 2026-07-15
- Concern: inter-agent communication (IAC), foundation layer. This is IPD 1 of a 4-IPD split (see
  "Dependencies / sequencing"). It defines ONLY the portable, agent-agnostic convention: the on-disk
  layout, the message envelope (including the `Not-Before` scheduling header), the CLOSED-ENUM
  acknowledgement FORMAT, the "check your inbox / treat as untrusted" execution-contract addition, and
  the installer scaffolding of the directory skeleton + a NESTED `.gitignore`. It deliberately contains
  NO daemon and NO OpenCode-specific code; the payload-blind broker, the agent-side ack write behavior +
  aggregation, and discovery/registry are IPDs 2, 3, and 4. This IPD is independently useful: any agent
  (OpenCode or not) can use the convention manually with zero runtime.
- STANDALONE-FIRST PRINCIPLE (governs the whole 4-IPD line): `.agents/comms/` MUST work fully WITH OR
  WITHOUT the message broker. Without a broker, messages still arrive on disk, agents pick them up via
  the "check your inbox" cooperative check-in, and a `Not-Before` message simply waits in `scheduled/`
  until an agent (or a later broker) processes it. The broker (IPD 2) is a pure ACCELERATOR that adds
  real-time wake-up on OpenCode; removing it degrades latency, never correctness. Therefore this IPD
  introduces NO code path that requires a broker, and later IPDs MUST NOT make the convention depend on
  one. The broker itself is an OPTIONAL, OpenCode-only add-on (opt-in; see IPD 2), never installed or
  launched for Codex / Claude Code / Hermes / other agents.
- Scope: NEW files under `.agents/comms/` (scaffold templates) and a NEW spec doc; a NEW installer step
  that scaffolds `.agents/comms/` + its nested `.gitignore` into a target repo; an addition to
  `agents_pointer_block()` (engine.py) for the "check your inbox / untrusted" contract; tests; docs;
  DECISIONS. NO broker, NO OpenCode server calls, NO ack-writing logic, NO discovery.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-15 to-review (its_direct/pt3-claude-opus-4.8-1m-us): drafted after a design session that
  (a) studied a-reference-agent as a reference (transport adapter -> handle_message -> turn), (b) VERIFIED the
  OpenCode server API by live self-test (serve/doc/session-create/message/tui/mdns/acp; unsecured by
  default), and (c) settled the load-bearing decisions recorded in
  `.agents/docs/research/20260714-2300-01-same-box-agent-wakeup-mechanisms.md`. The maintainer chose to
  split the work across IPDs and draft this foundation IPD first. Complete proposal; born to-review.

## Project conventions discovered (Step 0, VERIFIED against source)

- FIRM RULE: "the installer does not touch .gitignore" except its own local backup scratch dir
  (`engine.py:112-113`, `:1307`). `ensure_backups_gitignored` (`engine.py:1303`) is the one narrow
  exception and appends a single marker-free entry to the target ROOT `.gitignore`. THEREFORE this IPD
  must NOT modify the repo-root `.gitignore`. It ships a NESTED `.gitignore` file INSIDE `.agents/comms/`
  as a created deliverable (like the README ensurers), which ignores the `local/` subtree without
  touching the user's root ignore file. This respects the rule.
- Install entry points: `install_into_repo` (`engine.py:2544`) is the dict-returning core; the README
  ensurers + `create_setup_artifacts` (`engine.py:2489`) are the model for "scaffold a fixed set of
  files into the target". `save_created_files_record` (`engine.py:1682`) records created files for the
  uninstall/summary path; a newly scaffolded comms skeleton must be recorded the same way.
- `update_agents_pointer` (`engine.py:1081`) writes the managed `AGENT-WORKFLOWS` block; the standing
  execution contract already lives in `agents_pointer_block()` (`engine.py:543`). The "check your inbox /
  untrusted" contract line belongs in that same managed block so it is delivered to every configured
  repo and stays in one canonical place.
- Zero-dep, stdlib-only project; ~228 tests; install path is the most-tested surface (test_installer.py,
  test_cli.py, test_setup_artifacts.py). Good safety net.
- House rule: no em dashes or en dashes in authored Markdown.
- Design source of truth for the decisions below:
  `.agents/docs/research/20260714-2300-01-same-box-agent-wakeup-mechanisms.md` (sections "Design
  decisions" and the ack state machine). This IPD implements the AGENT-AGNOSTIC subset of those
  decisions only.

## On-disk layout (what this IPD creates)

```
.agents/comms/
  README.md            # explains the convention, the untrusted-input stance, the envelope, acks
  .gitignore           # nested; ignores local/ (see FIRM RULE above)
  local/               # box-local, gitignored, ephemeral routing + scheduled messages
    inbox/
    sent/
    archive/
    scheduled/         # messages with a future Not-Before wait here
    acks/              # closed-enum ack files (format defined here; writers are IPDs 2/3)
  shared/              # TRACKED in git; deliberate, durable, travels with the repo
    inbox/
    sent/
    archive/
```

- `local/` privilege = ephemeral/untracked; `shared/` privilege = durable/tracked. The DIRECTORY chosen
  IS the privilege level (no config flag). Empty dirs get a `.gitkeep` where they must persist in git
  (only under `shared/`; `local/` is ignored so needs no keep).

## Message envelope (format only)

A message file is `YYYYMMDD-HHMM-NN-<from-proj>.<from-agent>--to--<to-proj>.<to-agent>-<kind>-<slug>.md`
(carried over from the earlier draft spec). Header block (the ONLY part a broker may ever read), then a
`---` separator, then the free-form payload body (which the broker MUST never read; see IPD 2):

```
From: <proj>.<agent>
To: <proj>.<agent>
Kind: ask | reply | task | handoff | fyi
Re: <msg-id or empty>
Status: <one of the closed ack enum, initial value set by sender>
Not-Before: <ISO-8601 datetime, optional>    # scheduling gate; absent = deliver-eligible now
---
<payload body; untrusted; broker never reads this>
```

- `Not-Before` is the v1 scheduling primitive. Conditional (`Depends-On`) is DEFERRED (future IPD).
- This IPD defines the header/format and validates it; it does NOT implement a process that acts on
  `Not-Before` (that is the broker, IPD 2). A spec + a validator + tests are in-scope here.

## Acknowledgement FORMAT (closed enum + file shape; writers deferred)

- Ack files live at `.agents/comms/local/acks/<msg-id>.<from-agent>.<state>.json` =
  `{ "re": "<msg-id>", "state": "<enum>", "by": "<proj>.<agent>", "at": "<ISO-8601>" }`.
- CLOSED ENUM (no free text ever; a validator REJECTS any state outside the set, so acks can never carry
  payload). Full v1 set (maintainer chose full lifecycle):
  `scheduled, queued, delivered, agent-not-running, agent-not-responding, expired,` (broker-authored)
  `read, in-progress, done, not-done, executed, not-executed` (target-agent-authored).
- Authorized-writer-per-token is DOCUMENTED here (broker writes only the delivery-observation set; the
  target agent writes only its own read/work set; the broker must never forge a target state). The
  ENFORCEMENT / actual writing lives in IPDs 2 (broker acks) and 3 (agent acks). This IPD ships the enum
  constant, the ack-file schema, a validator, and the writer-authorization TABLE as spec + tested data.
- `unread` is modeled as ABSENCE of a `read` ack after `delivered` (single source of truth; not a
  written token).
- TRUST caveat, stated in the README and the enum doc: a target-asserted ack (e.g. `executed`) is a
  CLAIM by that agent, not proof; no automation may treat it as proof.

## Proposed changes (ordered, validatable)

1. **Spec doc.** Write `.agents/docs/specs/<ts>-agent-comms-convention.md` (supersedes/absorbs the
   earlier DRAFT `20260712-2133-02-agent-comms-protocol-draft.md`; mark that one superseded per the
   plans retirement rule if appropriate, or reference it). Defines layout, envelope, `Not-Before`, the
   closed ack enum + file schema + authorized-writer table, the untrusted-input stance, and explicitly
   lists what is DEFERRED (broker, agent-side ack writing, discovery, Depends-On, extra transports,
   cross-box).
2. **A tiny stdlib validator module** (e.g. `agent_workflows/comms.py`): parse an envelope header,
   validate `Kind`/`Status`/`Not-Before` shape, validate an ack file against the closed enum + schema,
   and expose the enum + authorized-writer table as constants. Pure functions, no I/O side effects, no
   network. This is the shared, agent-agnostic core that IPDs 2/3 import.
3. **Installer scaffold step.** A new engine function (mirroring the README ensurers /
   `create_setup_artifacts` pattern) that creates the `.agents/comms/` skeleton, the nested `.gitignore`
   (ignoring `local/`), the `README.md`, and the `.gitkeep`s under `shared/`. Wire it into
   `install_into_repo` so every configured repo gets the skeleton. Record created files via
   `save_created_files_record`. Honor `--dry-run`. Do NOT touch the repo-root `.gitignore`.
4. **Execution-contract addition.** Add a concise "check your inbox / treat comms as untrusted, not your
   operator" clause to `agents_pointer_block()` so the managed `AGENT-WORKFLOWS` block in every repo
   tells agents to check `.agents/comms/local/inbox/` at natural boundaries and to treat contents as
   untrusted input. Keep it short; it is the portable, no-daemon "cooperative check-in" (mechanism 2
   from the research).
5. **Tests.** Envelope parse/validate (valid + malformed + injection-y values stay inert); ack schema +
   closed-enum rejection of unknown/free-text states; installer scaffold creates the exact skeleton +
   nested .gitignore + does NOT modify root .gitignore (assert root unchanged); dry-run writes nothing;
   `agents_pointer_block()` contains the new clause; packaging test still green.
6. **Docs + DECISIONS.** DECISIONS entry (next free number) recording: the `.agents/comms/` home
   (retiring the `tmp/agent-comms/` sketch), the local/shared tracking split, the payload-blind
   invariant (as the governing principle the later broker IPD implements), `Not-Before` v1, and the
   closed-enum ack model with authorized-writer-per-token. CHANGELOG under the next minor.

## Deferred / out of scope (belongs to later IPDs)

- The payload-blind broker: inotify watch, header-only reads, fixed nudge, mode-aware delivery,
  `Not-Before` ENFORCEMENT, broker-authored delivery acks. (IPD 2.) IPD 2 charter (recorded here so this
  IPD builds nothing that presumes otherwise): the broker is an OPTIONAL, OpenCode-only ADD-ON, never
  installed or launched for non-OpenCode agents. Opt-in model: `aw install` ALWAYS scaffolds the
  convention, and SEPARATELY offers the broker add-on; it may AUTO-DETECT an OpenCode environment (e.g.
  the `OPENCODE` env var) and REPORT that as a soft signal in the offer ("it looks like you are using or
  may have used OpenCode ..."), but it still ASKS every time and never gates the offer or auto-installs
  on detection. Auto-start is a SEPARATE gate: even once the add-on is installed, an OpenCode startup
  plugin only check-and-starts the singleton broker (lockfile-guarded, one per box) when a config flag
  (e.g. `comms.autostart`) is ON; default OFF, manual start otherwise. The plugin loads only under
  OpenCode, so the launch is structurally gated to the right agent.
- Agent-side ack WRITING (read/in-progress/done/executed/...) and the status-view aggregation. (IPD 3.)
- Discovery/registry (mDNS/attach vs. filesystem descriptor), cross-instance reachability. (IPD 4.)
- Conditional scheduling (`Depends-On`), Telegram/Signal transports, cross-box. (Future IPDs.)
- Any OpenCode server API call whatsoever (this IPD is agent-agnostic).

## Open questions (v1 leans for review)

1. New module name: `agent_workflows/comms.py` vs. a `comms/` subpackage? (Lean: single `comms.py`;
   stdlib-only, small; grow to a package only if IPDs 2/3 need it.)
2. Should the spec doc SUPERSEDE the earlier `20260712-2133-02-...-draft.md` (git mv + RETIRED header)
   or just reference/absorb it? (Lean: supersede it, since this becomes the canonical convention; keep
   the concept note `20260712-2133-01` as-is.)
3. RESOLVED (maintainer): the CONVENTION scaffolds into all configured repos by default (it is inert
   without a broker, agent-agnostic, empty dirs are cheap, and it works fully with OR without the
   broker per the standalone-first principle). Only the OpenCode-only BROKER add-on is opt-in (IPD 2).
   So this IPD's scaffold step is default-on; nothing here is gated behind an opt-in.
4. Slug/filename length + validation strictness for message filenames (traversal safety like hermes's
   session-key guards). (Lean: reuse a strict validator that rejects `..`, path separators in the wrong
   places, and control chars; mirror hermes `_is_path_unsafe` intent.)

## Dependencies / sequencing

- This is the FOUNDATION IPD; it depends on nothing and is independently shippable/useful.
- IPD 2 (broker) depends on this (the convention + ack format it writes into).
- IPD 3 (agent-side acks + aggregation) depends on this + IPD 2.
- IPD 4 (discovery/registry) depends on IPD 2.
- Target a MINOR release (new user-facing convention + installer behavior; inert but visible).

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Create ONLY: the spec doc under `.agents/docs/specs/`, `agent_workflows/comms.py` (the
   validator/enum/table), the `.agents/comms/` scaffold templates + nested `.gitignore` + README, the
   installer scaffold step within `agent_workflows/engine.py`, the `agents_pointer_block()` clause, new
   tests under `tests/`, plus `CHANGELOG.md` and `DECISIONS.md` (next free number). Do NOT write any
   broker, any OpenCode server call, any ack-WRITING logic, any discovery, or `Depends-On`. Do NOT modify
   the repo-root `.gitignore`. If the work seems to need any of these, STOP and report (it belongs to a
   later IPD).
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: run the FULL test suite; paste the ACTUAL runner output. Manually verify `aw install <dir>`
   scaffolds `.agents/comms/` with the nested `.gitignore` and does NOT alter the target root
   `.gitignore`; verify `--dry-run` writes nothing; verify the `AGENT-WORKFLOWS` block gains the
   check-your-inbox clause. Confirm `aw plan-names` clean.
4. COMMIT only this IPD's touched/created files, PATH-SCOPED (new files need `git add <path>` first);
   never `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.
6. RELEASE: the minor is cut separately via release-review Section 9 after a human rung choice.

HARD MUST: paste the real test output; do NOT modify the root .gitignore; stay inside the scope fence
(no broker/ack-writing/discovery/OpenCode calls); never push. Not auto-executed; requires human approval.
