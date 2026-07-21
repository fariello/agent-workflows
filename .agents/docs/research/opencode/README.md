# .agents/docs/research/opencode/

OpenCode-capability research that grounds this framework's design, especially the filesystem
agent-comms protocol trial (now the canonical convention `../../specs/20260715-1722-01-agent-comms-convention.md`).

## Provenance and status

The research reports here are EXTERNAL artifacts produced with GPT-5.6 on 2026-07-13, against a pinned
OpenCode baseline (v1.17.18, commit `b1fc811`). They are kept VERBATIM: their own formatting and
punctuation are preserved, so the no-em-dash house rule that applies to authored framework Markdown
does NOT apply to these cited external reports. Treat them as reference/for-consideration input, not as
this repo's authoritative claims. A key honest caveat carried in the reports: no live OpenCode binary
was available in the research sandbox, so runtime claims are source-derived (from immutable commit
links) unless explicitly labeled otherwise, and live two-instance testing is still required before
relying on them.

## Verbatim caveat (honest note)

These are kept verbatim EXCEPT: on first staging, before the pre-commit config was updated to exclude
`.agents/docs/research/`, the ruff-format hook incidentally reformatted the two prototype Python files
(`prototype/broker/broker.py`, `prototype/tests/test_broker.py`) - whitespace/quote/line-wrap
normalization only, no semantic change. The pristine as-delivered copies were not retained, so those
two files reflect ruff-normalized formatting rather than strict as-delivered formatting; their content
is otherwise intact. All other files are as delivered. Pre-commit now excludes this path from the
content-mutating hooks so it will not recur.

## Contents

- `20260713-0900-...-inter-instance-agent-communication-research-prompt.md` (+ `.v2.md`): the deep-
  research prompts that were run.
- `20260713-1330-gpt56-...-inter-instance-agent-communication/`: the research answer package. How one
  running OpenCode instance can drive another (HTTP server API: create/prompt/status/abort/SSE), and
  crucially what OpenCode does NOT provide: no native peer provenance, no authentication, no durable
  peer mailbox, no distinct peer message role - an API prompt is indistinguishable from human input.
  Includes numbered sections (00-06), `sources.md`, and a `prototype/` (a broker, an `opencode-peer`
  plugin, a message JSON schema, and tests) sketching a richer transport that could layer ON TOP of the
  filesystem floor.

## Why this lives here (relevance to agent-workflows)

It underpins the agent-comms trial. Notably it VALIDATES the trial spec's stance: since OpenCode gives
no trustworthy peer provenance and no authentication, treating incoming messages as untrusted, keeping
the human as the backstop, and holding sender identity as unverified are the correct defaults. The
prototype is a candidate future upgrade transport, not a commitment; formalization remains gated per the
spec.

## Also here (reference, written for ocman)

- `20260713-1254-...-filesystem-runtime-artifacts-research-prompt.md` (the prompt, verbatim) and
  `20260713-1319-gpt56-...-filesystem-runtime-artifacts-reference-research.md` (the report): a deep
  reference on OpenCode's on-disk model (SQLite storage/WAL, layered config merge, snapshot repos,
  data/config/cache/state paths). This report was written FOR the `ocman` project and recommends ocman
  changes; it is archived here only as useful OpenCode-internals REFERENCE (it informs this framework's
  thinking, e.g. the agent-comms trial). A framing header at the top of the report says so. The
  authoritative copy for ocman lives in the ocman project; read its "ocman should ..." items as
  ocman-directed, not agent-workflows tasks.
