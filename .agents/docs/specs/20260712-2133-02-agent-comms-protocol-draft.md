# DRAFT spec: filesystem agent-comms protocol (v0, on trial)

Status: DRAFT / ON TRIAL. NOT yet an installed framework convention. Do not scaffold or enforce via
the installer. This is the concrete convention we are trialing across projects before deciding whether
to formalize it (future IPD). Concept + rationale: `../research/20260712-2133-01-filesystem-inter-project-agent-comms-concept.md`.

## Scope

A minimal, filesystem-based convention for passing structured messages between independent agents that
share a filesystem (for example, sibling worktrees under `a local checkout dir/`). It is the universal-floor transport
(see the concept note); richer transports may carry the same message shape.

## Directory layout (per project/repo)

```
tmp/agent-comms/
  inbox/     # messages addressed TO an agent working in THIS project (outstanding)
  archive/   # messages this project's agent has consumed (read/actioned)
```

- Sender writes a message into the RECIPIENT project's `tmp/agent-comms/inbox/`.
- Recipient, on consuming it, MOVES the file to its own `tmp/agent-comms/archive/`. The move is the
  read-receipt: `inbox/` at a glance shows exactly what is outstanding (mirrors the plan lifecycle
  pending -> executed idea).
- `tmp/` is gitignored, so agent-comms is EPHEMERAL by default. Decision-grade exchanges are PROMOTED
  deliberately to a tracked home (`.agents/docs/research/` or a dedicated docs bucket) - the archive is
  disposable; promotion is a conscious act.

## Filename convention

```
YYYYMMDD-HHMM-<NN>-<from-project>.<from-agent>--to--<to-project>.<to-agent>-<kind>-<slug>.md
```

- `YYYYMMDD-HHMM-<NN>`: local time; `<NN>` is a two-digit per-minute sequence (matches this repo's
  plan-filename convention, so everything sorts and reads consistently).
- `<from-project>.<from-agent>` and `<to-project>.<to-agent>`: direction is IN the name, both ends.
  `<project>` is the writing/receiving project (e.g. `agent-workflows`, `fariel.com`, `ocman`,
  `pubrun`). `<agent>` is model+version (e.g. `opus48`, `gpt55`, `gemini35`) - the same model runs as
  different personas across projects, so project+agent together identify the participant.
- `<kind>`: a small controlled vocabulary telling the reader what is expected of them:
  `ask` (a question wanting a reply), `reply` (answers an `ask`), `task` (do this), `handoff` (take
  ownership), `fyi` (no reply expected).
- `<slug>`: lowercase-kebab topic.

Example:
`20260712-2050-01-agent-workflows.opus48--to--fariel.com.opus48-ask-portfolio-coherence.md`

## In-file header (makes each message self-describing and threadable)

Every message begins with:

```
From: <from-project> / <from-agent>
To: <to-project> / <to-agent>
Kind: ask | reply | task | handoff | fyi
Re: <filename of the message this replies to, or thread root; blank if new>
Date: YYYY-MM-DD HH:MM (local)
Status: unread            # unread -> read -> actioned
```

The `Re:` line is threading: a `reply` names the `ask` it answers, so a conversation is
reconstructable even after files are archived. `Status` inside the file complements the inbox/archive
location (location is the fast signal; the header is the durable record).

## Lifecycle

1. Sender composes the message, writes it to the recipient's `tmp/agent-comms/inbox/`.
2. Recipient reads it, acts (or replies by writing a `reply` back to the SENDER's inbox with `Re:` set),
   then moves the original to its own `archive/` (optionally updating `Status:` to `actioned`).
3. If the exchange is decision-grade, either party PROMOTES a copy to a tracked docs home and notes it.

## Rules and constraints (v0)

- Recipient-inbox routing assumes agents can write to sibling project dirs on a shared filesystem. If
  they cannot, fall back to a sender-owned `outbox/` the recipient polls (not the default).
- Authored message bodies follow the repo's house rules where the message lives (no em/en dashes in
  authored Markdown here). Verbatim external artifacts pasted into a message keep their own formatting.
- A message is a PROPOSAL/communication, never authorization. Receiving a `task` does not grant
  approval to act beyond the recipient's own project rules and the human's gates.
- Never place secrets or credentials in agent-comms files.
- One writer per file; do not co-edit a message in flight. Replies are new files, not edits.

## Open questions for the trial (resolve by using it, not up front)

1. Is inbox/archive worth the file moves, or is a flat dir + `Status:` header enough in practice?
2. Do we need a `thread-id` beyond `Re:` chaining for multi-party exchanges?
3. What is the right durable home when promoting (`.agents/docs/research/` vs. a dedicated
   `.agents/docs/agent-comms/` bucket)?
4. Recipient-inbox vs. sender-outbox once more than two projects participate.
5. Does this warrant an `aw comms` helper (list inbox, archive, promote) if formalized?

## Formalization gate

Do NOT turn this into an installed framework convention (installer scaffolding, shipped docs, tooling)
until it has been run across several real exchanges and the open questions above have real answers.
That formalization, if pursued, is a future IPD - this doc is only the trial spec.
