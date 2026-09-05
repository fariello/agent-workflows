- Id: lsztiu
- Status: open
- Set: awinbox
- Priority: medium
- Work-Kind: feature
- Summary: add 'aw adopt' to file a raw .aw/inbox/ drop into a typed records tree (mint id6, derive conforming name, write front matter, move), with a suggest-then-confirm flow and a leak-sanitizer gate

## Workflow history
- 2026-09-05 created (aw backlog): add 'aw adopt' to file a raw .aw/inbox/ drop into a typed records tree (mint id6, derive conforming name, write front matter, move), with a suggest-then-confirm flow and a leak-sanitizer gate

Context: `.aw/inbox/` is a gitignored drop zone for RAW, not-yet-conforming external material,
established in commit b534fee9 (sited OUTSIDE `.aw/records/` so the record sweep cannot enumerate a
drop as an artifact). Today adopting a drop is entirely manual: choose a type/kind/slug/set, mint an
id6, derive the name per the uniform grammar, write front matter, move the file, refresh the index.
That is exactly the kind of hand-naming the artifact-organization specs forbid elsewhere.

Proposed surface (preview by default, `--apply` to write, per the house writing-command safety
pattern):

    aw adopt .aw/inbox/<file> --type research --kind research-report \
        --slug <slug> [--model <model>] [--set <setid>]

Behavior:
- Mint a collision-checked id6 and derive the conforming filename from the existing grammar
  (`YYYYMMDD-<setid>-NN-<id6>-<slug>[.<model>].<kind>.md`). Reuse `artifact_core` (it already owns
  the id6 primitive, the shard date math, and the preview/`--apply` pattern) rather than
  reimplementing naming.
- Write the type's starter front matter, preserving the body VERBATIM. Externally-produced artifacts
  are archived as-is; `.aw/records/research/README.md` already exempts them from the house no-em-dash
  rule, so no prose rewriting.
- Move (not copy) the file into `records/<type>/` and refresh the relevant index.

MAINTAINER DECISIONS (2026-09-05), which the implementation must honor:
1. REMOVE THE ORIGINAL on success. Keeping it means two durable copies of the same content, where the
   inbox copy has no id6 (so nothing can cite it) and the two can silently drift. Deleting it also
   keeps the inbox a queue of genuinely outstanding work, which is what makes an inbox count
   meaningful.
2. RUN THE LEAK-SANITIZER BEFORE WRITING and refuse on a `fail`. Adoption is the moment unvetted
   external text crosses into permanent tracked history, so this is the only point where the mistake
   is still reversible. BUT because the sanitizer has false positives, the refusal must be an
   INTERACTIVE ask with an explicit override flag (the established house pattern), not a hard wall:
   report the findings, let the human judge, and provide a documented `--allow-leaks`-style escape
   that is recorded in the adoption note.
3. SUGGEST, THEN CONFIRM the metadata. The agent proposes `--type`/`--kind`/`--slug`/`--set` from
   reading the document and shows them for approval before anything is written; it must NOT guess
   silently and must NOT bulk-adopt an inbox. A raw drop states none of this reliably, so a silent
   guess produces exactly the misnamed/miscategorized corpus the naming grammar exists to prevent.

Open questions for design time:
- Should `aw adopt` accept a path outside `.aw/inbox/` (e.g. an arbitrary file), or is the inbox the
  only legal source? Restricting it keeps the verb's meaning crisp.
- Does adoption record provenance (that the file came from an external model/service, and when)? A
  `source:`/`adopted-from:` front-matter facet would make the external origin machine-readable
  instead of prose, which matters given the untrusted-input stance.
- Multi-file adoption of a comparison set (several models answering one prompt) maps onto
  `aw research new-comparison`; decide whether `adopt` composes with that or stays single-file.

Related: open item `oxjt1d` (apply the artifact-organization model to further trees) anticipates the
same `artifact_core` reuse, so this should not invent a parallel mechanism.
