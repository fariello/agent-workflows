- Id: lsztiu
- Status: graduated
- Set: awinbox
- Priority: medium
- Work-Kind: feature
- Summary: add 'aw adopt' to file a raw .aw/inbox/ drop into a typed records tree (mint id6, derive conforming name, write front matter, move), with a suggest-then-confirm flow and a leak-sanitizer gate

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan lznpv6 (awinbox-01), implementing all three maintainer decisions as decided. See the RE-MEASUREMENT section appended. Every piece of machinery this item says to reuse was verified to exist: no adopt verb; artifact_core has every naming primitive; aw research new already implements the adjacent surface with the same flag vocabulary and preview/--apply default; aw research new-comparison scaffolds a multi-model set; and the leak sanitizer already has the exact fail/warn two-tier posture decision 2 needs, so that half consumes an existing design rather than adding one. ONE CONSTRAINT ADDED that this item does not state and that is the sharpest correctness edge: a raw body may contain a '- Id:' line, and AGENTS.md warns that honoring one 'would forge an identity claim that collides with a real artifact', so the verb must mint fresh against a REPOSITORY-WIDE collision set and never adopt an id6 from the body. TWO open questions answered from evidence: the comparison-set case is LIVE (two topics each present as three model variants in the inbox), and the verbatim-body requirement has an existing authority to cite in the research README. ONE GAP FOUND: .aw/inbox/ has no README, so the adoption contract lives only in AGENTS.md prose.
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

## RE-MEASUREMENT AND ONE ADDED CONSTRAINT, 2026-09-08 at HEAD a2e0438a during graduation

EVERY PIECE OF MACHINERY THIS ITEM SAYS TO REUSE WAS VERIFIED TO EXIST, by symbol and by running the
adjacent commands, rather than trusted:

  * NO `adopt` VERB EXISTS. `aw adopt` reports `invalid choice: 'adopt'`; `adopt` appears nowhere in
    `cli.py`.
  * `artifact_core` HAS EVERY PRIMITIVE: `generate_id6(existing, ...)`, `is_valid_id6`,
    `iter_id6_in_text`, `shard_dirname`, `shard_for_date`, `is_valid_shard_dirname`.
  * `aw research new` ALREADY IMPLEMENTS THE ADJACENT SURFACE, taking
    `--kind/--slug/--summary/--set/--model/--topic/--priority/--date`, dry-run by default with
    `--apply`, described as "Create a correctly-named research doc (per the naming grammar) plus
    starter front matter". `aw research new-comparison` scaffolds a multi-model set sharing a set id.
  * THE LEAK SANITIZER ALREADY HAS THE EXACT TWO-TIER POSTURE decision 2 requires: `fail` patterns
    "fail the non-interactive gate (pre-commit + CI)" while the softer tier should "confirm, never fail
    CI", and `Finding.severity` is `"fail" | "warn"`. So that half consumes an existing design.
  * THE INBOX IS REAL AND NON-EMPTY: 10-plus files, gitignored at `.aw/.gitignore:28` (`/inbox/`).

ONE CONSTRAINT ADDED THAT THIS ITEM DOES NOT STATE, and it is the sharpest correctness edge in the
work. This item says to "write the type's starter front matter", but a raw external document may
ALREADY contain something that looks like front matter, including a `- Id:` line. `AGENTS.md` warns
that such a line in an inbox file "is almost always a QUOTED EXAMPLE, and honoring it would forge an
identity claim that collides with a real artifact". So the verb must MINT a fresh id6 and must NEVER
adopt one found in the body, and the collision set must be REPOSITORY-WIDE (the id6 invariant is
cross-tree and fail-closed via `check.id6-collision` and `check.id6-identity-slot`), not scoped to the
destination tree. Without this, the verb's first real use could collide with a live artifact's
identity, after the original has already been deleted. Plan `lznpv6` E-02 owns it and E-07 tests it.

TWO THINGS FOUND THAT ANSWER THIS ITEM'S OWN OPEN QUESTIONS FROM EVIDENCE.

FIRST, THE COMPARISON-SET QUESTION IS LIVE, NOT HYPOTHETICAL. The inbox currently holds TWO topics each
present as three model variants (`agent-skill-runtimes-research` in gemini/gpt/sonnet forms, and
`aw-artifact-metadata-storage-research-report` likewise). So the very first real use of this verb will
be three adoptions that ought to share a set id. The graduated plan recommends COMPOSITION (the verb
gains `--set`, which the name derivation already consumes, and the human passes the same setid three
times) rather than teaching `adopt` a second group mode, and escalates the group-mode question.

SECOND, THE VERBATIM-BODY REQUIREMENT HAS AN EXISTING AUTHORITY TO CITE rather than restate:
`.aw/records/research/README.md:60` already exempts externally-produced artifacts from the house
no-em-dash rule because "their own punctuation and formatting are preserved".

ONE GAP FOUND THAT THIS ITEM DOES NOT MENTION: `.aw/inbox/` has NO README, unlike every records tree,
so the adoption contract currently lives only in `AGENTS.md` prose. A verb whose safety rules are not
written where its users look is a verb whose rules get violated. Plan `lznpv6` E-06 adds one, and notes
that the gitignore makes its committability a deliberate decision rather than an afterthought.

Confirmed still relevant: open item `oxjt1d` (apply the artifact-organization model to further trees)
anticipates the same `artifact_core` reuse, so the graduated plan adopts INTO existing trees and
reorganizes none.

GRADUATED to plan `lznpv6` (awinbox-01), which implements all three maintainer decisions as decided
(remove the original on success, leak-gate before writing with an interactive ask and a RECORDED
override, and suggest-then-confirm via the existing preview/`--apply` pattern). Its OQ-01 is RESOLVED
as restricting to the inbox, per this item's own leaning. Its OQ-03 leaves the multi-file group mode
open; if the maintainer wants it kept open for that, set this item `graduated` rather than `done`.
