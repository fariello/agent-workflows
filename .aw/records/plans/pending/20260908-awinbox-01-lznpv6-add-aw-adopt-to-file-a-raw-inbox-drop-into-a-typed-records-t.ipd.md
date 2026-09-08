# IPD: Add aw adopt to file a raw inbox drop into a typed records tree through a suggest-then-confirm flow with a leak gate

- Date: 2026-09-08
- Kind: child
- Concern: Adopting a raw `.aw/inbox/` drop is entirely manual, so the one moment unvetted external text crosses into permanent tracked history is the moment with no tooling, no gate, and no provenance. Today it means choosing a type/kind/slug/set by hand, minting an id6, deriving the name per the uniform grammar, writing front matter, moving the file, and refreshing the index. That is exactly the hand-naming the artifact-organization specs forbid everywhere else.
  VERIFIED AT HEAD `a2e0438a`: there is no `adopt` verb. `aw adopt` exits with `invalid choice: 'adopt'` and lists the 50-odd registered commands, and `adopt` appears nowhere in `cli.py`. The inbox is real and non-empty: `.aw/inbox/` currently holds 10-plus files, including three model-variant research reports on one topic, a `.tgz`, and an implementation prompt, and it is gitignored (`.aw/.gitignore:28`, `/inbox/`), sited OUTSIDE `.aw/records/` so the record sweep cannot enumerate a drop as an artifact.
  THE MACHINERY TO REUSE ALL EXISTS, which is what makes this tractable rather than speculative. `artifact_core` owns the id6 primitive (`generate_id6` with a collision set, `is_valid_id6`, `iter_id6_in_text`) and the shard date math (`shard_dirname`, `shard_for_date`, `is_valid_shard_dirname`). `aw research new` already implements the exact adjacent surface, taking `--kind/--slug/--summary/--set/--model/--topic/--priority/--date` with `--apply` and dry-run by default, and `aw research new-comparison` already scaffolds a multi-model comparison set sharing a set id, which is the shape three of the current inbox files have. The leak sanitizer already has a two-tier severity model where `fail` patterns fail the non-interactive gate and softer ones "confirm, never fail CI" (`leak_sanitizer.py:18-24`), and `Finding.severity` is exactly `"fail" | "warn"` (`:130-136`).
  THE MAINTAINER HAS ALREADY DECIDED THE THREE HARD PARTS (2026-09-05), so this plan implements rather than designs them: remove the original on success, run the leak sanitizer before writing and refuse on a `fail` but as an INTERACTIVE ask with a documented override rather than a hard wall, and SUGGEST then CONFIRM the metadata rather than guessing silently or bulk-adopting.
- Scope: Add `aw adopt` to file ONE raw inbox drop into a typed records tree: mint a collision-checked id6, derive the conforming filename from the existing grammar, write the type's starter front matter while preserving the body VERBATIM, move rather than copy, refresh the index, and record provenance. Preview by default with `--apply` to write. Reuse `artifact_core` for naming and the leak sanitizer for the pre-write gate; invent neither. EXCLUDES applying the artifact-organization model to further trees (backlog `oxjt1d`); excludes bulk adoption; excludes any change to the leak sanitizer's patterns or severities; excludes changing what `.aw/inbox/` is or its gitignore status.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/artifact_adopt.py, tests/test_artifact_adopt.py, .aw/records/backlog/README.md
- Item-Dependencies: none
- Status: to-review
- Set: awinbox
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: lznpv6
- From-Backlog: lsztiu

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `lsztiu`. The item carries no `- Blocks-Release:` so none is inherited or invented.
  EVERY PIECE OF MACHINERY THE ITEM SAYS TO REUSE WAS VERIFIED TO EXIST rather than trusted: `artifact_core.generate_id6`/`shard_dirname`/`shard_for_date` by symbol; `aw research new` and `aw research new-comparison`'s full flag surfaces by running `--help`; the leak sanitizer's two-tier `fail`/`warn` model and its documented "confirm, never fail CI" posture for the softer tier, which is EXACTLY the interactive-ask shape the maintainer's decision 2 requires and means that half needs no new concept; and the absence of any `adopt` verb.
  THREE THINGS I FOUND THAT THE ITEM DOES NOT SAY, each of which changes the work. FIRST, `.aw/inbox/` has NO README, unlike every records tree, so the one place a human or agent would look to learn the adoption contract does not exist; E-06 adds it, because a verb whose safety rules live only in a plan is a verb whose rules will be violated. SECOND, three of the current inbox files are the SAME research topic from three different models (`agent-skill-runtimes-research` in gemini/gpt/sonnet variants, and separately three `aw-artifact-metadata-storage-research-report` variants), which is precisely the comparison-set shape `aw research new-comparison` exists for, so the item's third open question is not hypothetical and OQ-03 answers it from the live inbox. THIRD, the research README already EXEMPTS externally-produced artifacts from the house no-em-dash rule, which is the authority for the item's "preserve the body VERBATIM" requirement and should be cited rather than restated.
  ONE DESIGN CONSTRAINT I ADDED, and it is the sharpest edge in this plan: the item says to write the type's starter front matter, but a raw external document may ALREADY contain something that looks like front matter, including a `- Id:` line. `AGENTS.md` warns explicitly that such a line in an inbox file "is almost always a QUOTED EXAMPLE, and honoring it would forge an identity claim that collides with a real artifact". So E-03 must MINT a fresh id6 and must never adopt an id6 found in the body, and E-05 tests exactly that case. Without this, the verb's first real use could collide with a live artifact's identity.

## Goal

Make adopting an inbox drop a single tooled, gated, provenance-recording act instead of six manual steps at the one boundary where unvetted text becomes permanent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the naming and identity core, reusing what exists

- [ ] E-01 CREATE THE ADOPTION MODULE AND DERIVE THE NAME FROM THE EXISTING GRAMMAR, reusing `artifact_core` rather than reimplementing naming. The target shape is the uniform grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>[.<model>].<kind>.md`.
  READ `aw research new` FIRST AND FOLLOW IT. It already solves this exact problem for one tree, including the optional `.<model>` facet, the `--date` override, the dry-run default and `--apply`. Whatever this verb does differently from that command should be a deliberate, stated difference, not an accident of writing it fresh. If the name derivation can be CALLED rather than copied, call it: a second name-deriver is how two spellings of one grammar appear.
  DO NOT INVENT A SECOND ID6 PRIMITIVE. `artifact_core.generate_id6(existing, ...)` already takes the collision set, and `iter_id6_in_text` already exists for building it. Use them.
  - Depends on: none
  - Expected outcome: a new module deriving a conforming filename for a given type/kind/slug/set/model/date, with the id6 minted through `artifact_core.generate_id6` against a real repository-wide collision set; the name derivation shared with `aw research new` or the divergence stated.
  - Execution state: pending

- [ ] E-02 MINT A FRESH id6 AND NEVER ADOPT ONE FOUND IN THE BODY. This is the sharpest correctness edge in the plan. A raw external document may contain something that looks like front matter, including a `- Id:` line, and `AGENTS.md` warns that such a line is "almost always a QUOTED EXAMPLE, and honoring it would forge an identity claim that collides with a real artifact".
  BUILD THE COLLISION SET FROM THE WHOLE REPOSITORY, not from the destination tree alone. The id6 invariant is repository-wide (`check.id6-collision` and `check.id6-identity-slot` are cross-tree and fail closed), so a set scoped to one tree would mint a duplicate that `aw check` then rejects after the file is already written and the original deleted.
  IF THE BODY CONTAINS AN id6-SHAPED TOKEN, REPORT IT IN THE PREVIEW rather than silently ignoring it, so a human can see that the document mentions an identity and that the verb is deliberately not using it. Silence here looks identical to not having checked.
  - Depends on: E-01
  - Expected outcome: the minted id6 is always fresh and never read from the body; the collision set is repository-wide; an id6-shaped token in the body is surfaced in the preview and explicitly not adopted.
  - Execution state: pending

### Task group 2: the three maintainer decisions, implemented as decided

- [ ] E-03 IMPLEMENT SUGGEST-THEN-CONFIRM FOR THE METADATA, which is maintainer decision 3. The verb proposes `--type`/`--kind`/`--slug`/`--set` from reading the document and shows them for approval BEFORE anything is written; it must NOT guess silently and must NOT bulk-adopt an inbox.
  THE PREVIEW IS THE CONFIRMATION SURFACE, and the house pattern already gives it: dry-run by default, `--apply` to write, exactly as `aw research new` and `aw research new-comparison` do. So "suggest then confirm" needs no new interaction model: the bare invocation SUGGESTS and the `--apply` invocation CONFIRMS. State that mapping explicitly so a later reader does not add a redundant prompt.
  WRITE THE STARTER FRONT MATTER BUT PRESERVE THE BODY VERBATIM. `.aw/records/research/README.md` already exempts externally-produced artifacts from the house no-em-dash rule on the grounds that "their own punctuation and formatting are preserved", which is the authority for verbatim preservation; cite it rather than restating the rule. Do not reflow, re-wrap, normalize dashes, or strip anything from the body.
  REFUSE A BULK INVOCATION EXPLICITLY. A verb that accepts a directory or a glob will eventually be pointed at the whole inbox, which the maintainer forbade and which `AGENTS.md` repeats ("never bulk-adopt an inbox silently"). Take exactly one path and refuse more than one with a message saying why.
  - Depends on: E-01
  - Expected outcome: a bare invocation previews the proposed type/kind/slug/set and writes nothing; `--apply` performs the adoption; the body is byte-identical after adoption; more than one input path is refused with a stated reason.
  - Execution state: pending

- [ ] E-04 RUN THE LEAK SANITIZER BEFORE WRITING AND MAKE THE REFUSAL AN INTERACTIVE ASK WITH A DOCUMENTED OVERRIDE, which is maintainer decision 2. Adoption is the moment unvetted external text crosses into permanent tracked history, so it is the only point where the mistake is still cheap to undo.
  THE TWO-TIER MODEL ALREADY EXISTS AND MAPS ONTO THIS EXACTLY, so consume it rather than inventing a policy: `leak_sanitizer` documents that `fail` patterns fail the non-interactive gate while the softer tier is meant to "confirm, never fail CI", and `Finding.severity` is `"fail" | "warn"`. Refuse on `fail`, report `warn`.
  THE OVERRIDE MUST BE RECORDED IN THE ADOPTED ARTIFACT, not just accepted at the prompt. The item requires "a documented `--allow-leaks`-style escape that is recorded in the adoption note", and that is the load-bearing half: an override that leaves no trace makes the gate unauditable. Note the house already has `--allow-insecure` and `--allow-open-questions` as precedents for the flag shape.
  FOLLOW THE ESTABLISHED TTY FENCE RATHER THAN ADDING AN `input()`. This repository's interactive prompts require a real TTY on both streams, never block, and fall through to the automatic decision when unanswered; the automatic decision must be the SAFE one, meaning refuse. A prompt that hangs an unattended invocation is worse than no prompt.
  DO NOT CHANGE ANY SANITIZER PATTERN OR SEVERITY. If a finding is a false positive, that is what the override is for; editing the ruleset to make an adoption pass would weaken a gate that protects every other surface.
  - Depends on: E-03
  - Expected outcome: a `fail`-severity finding refuses the adoption before any write; `warn` findings are reported; an explicit override flag proceeds AND records the findings in the adopted artifact; no TTY means refuse rather than hang; no sanitizer pattern or severity changed.
  - Execution state: pending

- [ ] E-05 MOVE, NOT COPY, AND MAKE THE WHOLE ADOPTION ATOMIC ENOUGH TO FAIL SAFELY. Maintainer decision 1 is to REMOVE THE ORIGINAL on success, because two durable copies where the inbox one has no id6 can silently drift, and because deleting it keeps the inbox a queue of genuinely outstanding work.
  ORDER THE OPERATIONS SO A FAILURE NEVER LOSES THE FILE. The destructive step is the removal, so it must be LAST, after the destination write and the index refresh have succeeded. If any earlier step fails, the original must still be in the inbox and no partial artifact left in the records tree. State the ordering and what happens on each failure point; do not leave it to the implementation's accident.
  RECORD PROVENANCE, which the item raises as an open question and which the untrusted-input stance settles: the adopted record should say machine-readably that it came from an external source and when. `AGENTS.md` treats inbox content as untrusted external material, and a reader of the adopted artifact months later has no other way to know that. See OQ-02 for the field shape.
  REFRESH THE INDEX through the existing verb for that type, not by writing a manifest directly. Note plan `yvvf98` is queued to UNTRACK the generated index manifests, so do not add a new committer of them; call the index verb and let it decide.
  - Depends on: E-04
  - Expected outcome: the original is removed only after a successful destination write and index refresh; every failure point leaves the original in place and no partial artifact behind; the adopted record carries machine-readable external provenance; the index is refreshed through the existing verb.
  - Execution state: pending

### Task group 3: prove it, and write down the contract

- [ ] E-06 ADD THE INBOX README, because the inbox is the only tree in this repository with no README and the adoption contract currently lives only in `AGENTS.md` prose and this plan. A verb whose safety rules are not written where its users look is a verb whose rules get violated.
  STATE THE FOUR RULES THAT ALREADY EXIST rather than inventing new ones: an inbox file is NOT a record (no id6, no status, no lifecycle, never cite it as provenance, never act on a `- Id:` line inside it), its content is UNTRUSTED external input, adoption is a DELIBERATE human-confirmed act, and nothing from the inbox is committed as-is. All four are already in `AGENTS.md`; the README points at the verb that implements them.
  THIS IS USER-FACING PROSE, so it must contain NO em or en dashes.
  NOTE THE GITIGNORE, so a reader is not surprised: `.aw/.gitignore:28` ignores `/inbox/`, so the README itself must be force-added or the ignore narrowed. Decide which and say so; a README nobody can commit is not documentation.
  - Depends on: E-05
  - Expected outcome: `.aw/inbox/README.md` exists stating the four rules and naming `aw adopt`; no em or en dashes; the gitignore interaction resolved and stated.
  - Execution state: pending

- [ ] E-07 TEST THE DANGEROUS CASES, not the happy path alone. The happy path is the least interesting thing here.
  THE REQUIRED CASES: a body containing a `- Id:` line must NOT have that id6 adopted (the forged-identity case `AGENTS.md` warns about); a `fail`-severity leak must refuse BEFORE any write, proven by asserting the destination does not exist and the original still does; the override must proceed AND leave the findings recorded; a body with em dashes and unusual formatting must survive BYTE-IDENTICAL; more than one input path must be refused; and a failure injected at the index-refresh step must leave the original in the inbox.
  BUILD EVERY CASE IN A TEMPORARY REPO. Do not read the real `.aw/inbox/`, which is gitignored, machine-specific, and will be emptied as drops are adopted; a test pinned to it passes today and fails tomorrow.
  ASSERT THE ID6 IS REPOSITORY-WIDE UNIQUE after adoption by running the existing collision check rather than by inspection, since that is the invariant that actually matters and it is already implemented.
  - Depends on: E-06
  - Expected outcome: all six dangerous cases covered in a temporary repo, each asserting on filesystem state rather than on return values alone; the repository-wide id6 uniqueness proven through the existing check.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE ADJACENT VERB ALREADY EXISTS AND IS THE TEMPLATE. `aw research new` takes `--kind/--slug/--summary/--set/--model/--topic/--priority/--date`, is dry-run by default with `--apply`, and its help says "Create a correctly-named research doc (per the naming grammar) plus starter front matter". `aw research new-comparison` scaffolds a multi-model set sharing a set id. Follow both.
- `artifact_core` OWNS THE PRIMITIVES: `generate_id6(existing, ...)`, `is_valid_id6`, `iter_id6_in_text`, `shard_dirname`, `shard_for_date`, `is_valid_shard_dirname`. The item is right that this must not be reimplemented.
- THE LEAK SANITIZER ALREADY HAS THE EXACT TWO-TIER POSTURE THIS NEEDS. Its module docstring states `fail` patterns "fail the non-interactive gate (pre-commit + CI)" while the softer tier should "confirm, never fail CI", and `Finding.severity` is `"fail" | "warn"`. So the interactive-ask requirement consumes an existing design rather than adding one.
- AN INBOX `- Id:` LINE IS A TRAP. `AGENTS.md` states it is "almost always a QUOTED EXAMPLE, and honoring it would forge an identity claim that collides with a real artifact". This is why E-02 exists as its own item.
- THE id6 INVARIANT IS REPOSITORY-WIDE AND FAIL-CLOSED (`check.id6-collision`, `check.id6-identity-slot`), so a tree-scoped collision set is insufficient.
- EXTERNAL ARTIFACTS ARE EXEMPT FROM THE HOUSE PROSE RULES. `.aw/records/research/README.md` records that "their own punctuation and formatting are preserved", which authorizes verbatim body preservation.
- THE INBOX IS GITIGNORED AND SITED OUTSIDE `.aw/records/` deliberately, so the record sweep cannot enumerate a drop as an artifact (`.aw/.gitignore:28`).
- INTERACTIVE PROMPTS IN THIS REPOSITORY REQUIRE A REAL TTY ON BOTH STREAMS, never block, and fall through to the automatic decision, which must be the safe one.
- DO NOT ADD A NEW COMMITTER OF THE GENERATED INDEX MANIFESTS: plan `yvvf98` is queued to untrack them.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `a2e0438a`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | N/A | `agent_workflows/cli.py` | No `adopt` verb exists: `aw adopt` reports `invalid choice: 'adopt'` and `adopt` appears nowhere in the CLI. | ran it; grepped `cli.py` |
| F-2 | N/A | `.aw/inbox/`, `.aw/.gitignore:28` | The inbox is real, gitignored, and holds 10-plus files awaiting adoption, so this is live work rather than speculative. | `ls`; `git check-ignore -v` |
| F-3 | N/A | `artifact_core.py` | Every naming primitive the item says to reuse exists by symbol: `generate_id6`, `is_valid_id6`, `iter_id6_in_text`, `shard_dirname`, `shard_for_date`, `is_valid_shard_dirname`. | grep by symbol |
| F-4 | N/A | `aw research new`, `aw research new-comparison` | The adjacent surface is already implemented with the same flag vocabulary, dry-run default and `--apply`, including the optional `.<model>` facet and a comparison-set scaffolder. | ran both `--help` |
| F-5 | N/A | `leak_sanitizer.py:18-24`, `:130-136` | The two-tier `fail`/`warn` model with "confirm, never fail CI" for the softer tier already exists, so the interactive-ask requirement needs no new concept. | source read |
| F-6 | HIGH | `AGENTS.md` inbox paragraph | AN INBOX `- Id:` LINE MUST NEVER BE ADOPTED: it is "almost always a QUOTED EXAMPLE, and honoring it would forge an identity claim that collides with a real artifact". The item does not mention this and it is the plan's sharpest correctness edge. | file read |
| F-7 | MED | `.aw/inbox/` | THE COMPARISON-SET CASE IS LIVE, NOT HYPOTHETICAL: two distinct topics each appear as three model variants (`agent-skill-runtimes-research` and `aw-artifact-metadata-storage-research-report`), which is exactly what `aw research new-comparison` scaffolds. The item raised this as an open question. | `ls .aw/inbox/` |
| F-8 | MED | `.aw/inbox/` | The inbox has NO README, unlike every records tree, so the adoption contract has nowhere a user would look. | `ls` |
| F-9 | LOW | `.aw/records/research/README.md:60` | Externally-produced artifacts are already exempt from the house no-em-dash rule because "their own punctuation and formatting are preserved", which is the authority for verbatim body preservation. | file read |
| F-10 | LOW | pending plan `yvvf98` | The generated index manifests are queued to be UNTRACKED, so a new verb must not become a new committer of them. | that plan's title and scope |

## Proposed changes (ordered, validatable)

1. E-01 creates the module and derives the conforming name by reusing `artifact_core` and following `aw research new`.
2. E-02 mints a fresh repository-wide-unique id6 and refuses to adopt one found in the body, surfacing it in the preview instead.
3. E-03 implements suggest-then-confirm as the existing preview/`--apply` pattern, preserves the body verbatim, and refuses bulk input.
4. E-04 gates on the leak sanitizer's existing `fail` tier with a recorded override and a safe no-TTY fallback.
5. E-05 moves rather than copies, orders the destructive step last, and records external provenance.
6. E-06 writes the inbox README stating the four existing rules.
7. E-07 tests the six dangerous cases in a temporary repo.

## Deferred / out of scope (with reason)

- APPLYING THE ARTIFACT-ORGANIZATION MODEL TO FURTHER TREES. Backlog `oxjt1d` (open), which the item names and which "anticipates the same `artifact_core` reuse, so this should not invent a parallel mechanism". This plan adopts INTO existing trees; it does not reorganize any.
- BULK ADOPTION. Forbidden by the maintainer's decision 3 and by `AGENTS.md` ("never bulk-adopt an inbox silently"). E-03 refuses it explicitly rather than leaving it unimplemented, because an unimplemented capability tends to get added later without the reasoning.
- CHANGING ANY LEAK-SANITIZER PATTERN OR SEVERITY. The override exists for false positives. Editing the ruleset to make one adoption pass would weaken a gate protecting every other surface.
- MULTI-FILE COMPARISON-SET ADOPTION. OQ-03. Deferred deliberately even though F-7 shows the case is live, because `aw research new-comparison` already scaffolds that shape and the right answer is probably to COMPOSE with it rather than teach `adopt` a second mode. Single-file first keeps the verb's meaning crisp, which is the item's own stated preference.
- ACCEPTING A PATH OUTSIDE `.aw/inbox/`. OQ-01. The item asks and leans toward restricting; this plan restricts, because it keeps the verb's meaning crisp and because the untrusted-input reasoning that justifies the leak gate is specifically about inbox content.
- CHANGING WHAT `.aw/inbox/` IS, its location, or its gitignore status. It is sited outside `.aw/records/` deliberately.

## Scope check

- Over-scope: `.aw/records/backlog/README.md` is declared ONLY if E-06's gitignore resolution requires documenting the inbox convention in a committed README instead of an ignored one; if the inbox README can be committed directly, that path is unmodified and must be acknowledged at finalize rather than edited to justify the declaration.
- Under-scope: stated rather than left as `none`. After this plan a comparison SET still requires three separate adoptions (OQ-03), and nothing reorganizes any tree (`oxjt1d`).

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. Every case in a temporary repo; never read the real `.aw/inbox/`, which is gitignored, machine-specific and will empty as drops are adopted. Run `aw check all` after an adoption in the temporary repo to prove the adopted artifact satisfies the repository-wide invariants (id6 uniqueness, naming grammar, front matter), since those checks are the real acceptance criteria and are already implemented. Run `aw sanitize --agent` on the adopted result too, since the whole point of E-04 is that adopted content is sanitizer-clean or explicitly overridden.

## Spec / documentation sync

The uniform artifact-naming grammar is owned by `.aw/records/specs/20260817-2147-01-uniform-artifact-naming-grammar.spec.md` and the artifact-organization model by the `artifact-organization` specs. THIS PLAN CONSUMES BOTH AND SHOULD AMEND NEITHER, because it derives names through the existing grammar rather than defining a new one; that is the justification to record.
TWO THINGS TO CHECK RATHER THAN ASSUME. FIRST, whether the naming-grammar spec enumerates the LEGAL SOURCES of a new artifact or the verbs that may create one; if it does, adding a creating verb touches that enumeration and the spec file must be declared in `- Scope-Paths:` before execution, since the runners announce declared spec edits before a run starts and the finalize scope gate reconciles declared against actual. SECOND, whether any spec defines the front-matter facet set for the destination types, because E-05's external-provenance field ADDS a facet; an additive change to a documented facet set still belongs in the record. Read both and report which.
`AGENTS.md` already documents the inbox and the adoption contract in prose, and that text is INSTALLED from `agent_workflows/engine.py`, so if this plan changes the contract it must edit the generator rather than `AGENTS.md`. It should not need to: this plan implements the documented contract rather than altering it. Do NOT edit spec `25kzda`'s §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Should `aw adopt` accept a path outside `.aw/inbox/`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as NO, restricting to the inbox, which is the direction the item itself leans ("Restricting it keeps the verb's meaning crisp"). The reasoning is not only tidiness: the leak gate, the untrusted-input stance, and the remove-the-original behavior are all justified specifically by the inbox being a drop zone for unvetted EXTERNAL material. Pointed at an arbitrary file, "move it and delete the original" becomes a destructive operation on something a human may not have intended as a draft, and the leak refusal becomes noise on in-repo content that is already committed. If a general "file this file as a record" verb is wanted later, it is a different verb with different defaults.

### OQ-02: What shape does the external-provenance record take?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-05 requires provenance be recorded machine-readably and any reasonable field shape satisfies that; the question is which. The item proposes a `source:`/`adopted-from:` front-matter facet, and the argument for a facet over prose is the item's own: it "would make the external origin machine-readable instead of prose, which matters given the untrusted-input stance". The constraint to check first is whether the destination type's front-matter facet set is DEFINED in a spec, because adding a facet to a specified set is a contract change (see the spec-sync section). If it is, either reuse an existing facet or declare the spec. Note the original filename is itself useful provenance and is about to be deleted, so capture it before the move.

### OQ-03: Does multi-file comparison-set adoption compose with `aw research new-comparison` or stay out?

- Blocking: no
- Status: open
- Owner: this plan's executor for the recommendation, the maintainer for the scope call
- Resolution or deferral rationale: NOT blocking, because single-file adoption is complete and useful on its own and the deferred section already excludes the multi-file mode. It is recorded because F-7 shows the case is LIVE: the inbox currently holds two topics each present as three model variants, so the very first real use of this verb will be three adoptions that ought to share a set id. The likely right answer is COMPOSITION, meaning `adopt` gains a `--set` argument (which E-01 already derives names from) and the human passes the same setid three times, rather than `adopt` learning to consume a group. That is nearly free and avoids a second mode. Recommend it and let the maintainer decide whether a real group mode is wanted.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the derived filename for at least three type/kind/slug/model combinations, showing each conforms to the grammar. Paste proof `artifact_core.generate_id6` was CALLED rather than reimplemented (show the call). State whether the name derivation is shared with `aw research new` or diverges, and if it diverges, say why.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste an adoption of a body containing a `- Id: abc123` line, showing the adopted artifact carries a DIFFERENT, freshly minted id6 and that `abc123` was surfaced in the preview as present-but-not-adopted. Paste the collision set's construction showing it is repository-wide, not destination-tree-scoped. Paste `aw check all` on the result showing no id6 collision.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the BARE invocation's output showing the proposed type/kind/slug/set and proving nothing was written (the destination does not exist, the original still does). Paste the `--apply` invocation. Paste a byte-comparison (a hash of the body before and after) proving the body is UNCHANGED, using a source body that contains em dashes and unusual formatting. Paste the refusal for two input paths with its message.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste an adoption attempt on a body carrying a `fail`-severity leak, showing it REFUSES and that the destination does not exist and the original is still in the inbox. Paste a `warn`-only case showing it reports and proceeds. Paste the override invocation showing it proceeds AND that the findings are RECORDED in the adopted artifact. Paste the no-TTY case showing it refuses rather than hanging. Paste a diff proving no sanitizer pattern or severity changed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the operation ORDER as implemented and, for EACH failure point (destination write fails, index refresh fails), paste a fault-injected run showing the original still in the inbox and no partial artifact in the records tree. Paste the successful case showing the original GONE and the artifact present. Paste the recorded external provenance and state OQ-02's answer. Paste proof the index was refreshed through the existing verb rather than by writing a manifest.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `.aw/inbox/README.md` as written. Paste a grep of it for em and en dashes returning nothing. State how the gitignore was resolved (force-add or narrowed ignore) and paste evidence the README is actually committable under that resolution.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste all six dangerous cases with actual runner output: the `- Id:` body, the `fail` leak refusal, the recorded override, the byte-identical body, the multi-path refusal, and the injected index-refresh failure. For each, paste the FILESYSTEM assertion, not only a return value. Paste proof no test reads the real `.aw/inbox/`. Paste `aw check all` and `aw sanitize --agent` on an adopted artifact in the temporary repo.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: the verb is not safe in parts. Its four safety properties (fresh id6 rather than a forged one, verbatim body, leak gate before the write, and original removed only after success) are each individually implementable but each is a precondition for the others being meaningful: a leak gate on a verb that forges an identity, or a verbatim body written by a verb that deletes the original before the destination write succeeds, is not a partial improvement but a new hazard. Shipping the naming core without the gate would give a working adoption path with no protection at exactly the boundary the maintainer identified as the only reversible one. The plan is nonetheless ordered so each E-item is independently reviewable, and E-01 and E-02 could be validated before the gate exists.

Scope fence: touch ONLY the four paths in `- Scope-Paths:`. Do NOT reimplement id6 minting, the naming grammar, or the shard math. Do NOT adopt an id6 found in a body. Do NOT change any leak-sanitizer pattern or severity. Do NOT accept a path outside `.aw/inbox/` (OQ-01, resolved). Do NOT implement bulk or multi-file adoption. Do NOT reorganize any tree (`oxjt1d`). Do NOT become a new committer of the generated index manifests (`yvvf98`). Do NOT hand-edit `AGENTS.md` instead of the generator. Do NOT edit spec `25kzda`'s §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `generate_id6`, `is_valid_id6`, `iter_id6_in_text`, `shard_dirname`, `shard_for_date`, `Finding`, `Ruleset`, and the `research new` / `research new-comparison` CLI registrations by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. NOTE THE GITIGNORE INTERACTION: `.aw/inbox/` is ignored, so E-06's README needs a deliberate decision about committability and must not be force-added without stating why. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved lznpv6 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `lsztiu`, which this plan carries as `- From-Backlog:`. That item carries no release gate, so none is inherited. Its multi-file comparison-set question (OQ-03) is NOT delivered here and is recorded as surviving work, so if the maintainer wants it kept open for that, set the item `graduated` rather than `done`.
