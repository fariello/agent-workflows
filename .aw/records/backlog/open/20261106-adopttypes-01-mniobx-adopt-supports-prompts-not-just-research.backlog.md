- Id: mniobx
- Status: open
- Blocks-Release: f33nrj
- Set: adopttypes
- Priority: high
- Work-Kind: bug
- Summary: aw adopt supports only the research tree: add prompts (and stop defaulting every inbox drop to research)

## Workflow history
- 2026-11-07 created (aw backlog): aw adopt supports only the research tree: add prompts (and stop defaulting every inbox drop to research)

## Problem

`aw adopt` can file an `.aw/inbox/` drop ONLY into the research tree (`SUPPORTED_TYPES = ("research",)`
in `agent_workflows/artifact_adopt.py`; `--type` help: "research is the only supported type on day
one"). Any other destination is refused, and with no `--type` the verb SUGGESTS `research`
unconditionally (`suggest_metadata`: `s_type = type_ or "research"`).

The inbox is the general drop zone for external material, and a large share of what lands there is
NOT research. Most commonly it is a staged PROMPT authored elsewhere (by an external LLM or by the
maintainer) that should land in `.aw/records/prompts/pending/`. The current verb therefore:

1. Mis-files by default. A prompt dropped in the inbox is previewed and, on `--apply`, adopted as a
   `research-report` (or `research-prompt` research kind if the filename contains "prompt") under
   `.aw/records/research/`, with research YAML front matter, a research `status: todo`, and an
   index entry. That is the wrong tree, the wrong metadata dialect, and the wrong lifecycle.
2. Leaves no tooled path for the correct destination. The only way to file a prompt drop properly
   is by hand: `aw prompts new --apply` to mint the name and `<!-- aw-prompt: ... -->` comment,
   append the body manually, verify the body, delete the inbox copy. That bypasses the leak gate,
   the already-adopted warning, the forged-id guard, and the move-last ordering that `aw adopt`
   exists to guarantee, i.e. exactly the hand-filing the inbox README forbids ("Adopt one with the
   tooled verb, never by hand").
3. Encourages an agent to pick research when research is the only type the verb supports. The
   suggestion is presented as a default rather than as one option among several, so an agent tends
   to accept it.

## Observed incident (2026-11-06, adopter repo acelm)

A maintainer dropped a prompt into `.aw/inbox/`. The agent ran `aw adopt`, accepted the suggested
type `research`, applied it (minting a research id6, writing research front matter, refreshing the
research index), and additionally ran `aw research add-model gpt-6 --apply` to clear an
index-check finding, which created a new tracked config file. The maintainer then had to correct the
type; the agent had to unwind the research artifact, the index entry, and the config file, then
re-file by hand through `aw prompts new` plus a manual body append. A second drop the same day was
filed entirely by hand for the same reason. Every step of the unwind and the hand-filing was outside
the verb's safety guarantees.

## Required outcome

`aw adopt` supports, at minimum, the prompts tree in addition to research, with the same guarantees
it gives research today:

- `--type prompts` (and a matching suggestion) files the drop under `.aw/records/prompts/pending/`
  by DELEGATING to the existing `aw prompts new` planner (no second name-deriver), writing the single
  leading `<!-- aw-prompt: ... -->` metadata comment and NO other front matter, so the body stays
  upload-ready (prompt purity, spec OQ-25). Supports `--kind run-once|research|session-handoff`,
  `--set`, `--slug`, `--concerns`, `--targets`, `--author`, `--status` (default `pending`).
- No `aw-adopt` provenance blockquote is inserted INTO a prompt body (that would break prompt
  purity). Provenance (original filename, adoption date, leak-scan result, any `--allow-leaks` rule
  names) is recorded in the metadata comment or a sidecar instead.
- The leak gate, the fresh-id6 / never-adopt-a-body-id guard, the already-adopted warning, the
  verbatim body, and remove-the-original-last all apply unchanged.
- Type SUGGESTION stops defaulting blindly to research. A filename ending `.prompt.md`, or containing
  `prompt`, or a body that addresses a target AI (imperatives, a deliverable section), suggests
  `prompts`. When the signal is ambiguous the preview says so explicitly and names the alternatives,
  rather than presenting research as settled.
- Wrong-type recovery is tooled: re-filing a just-adopted artifact into another tree (for example a
  `--retype`, or adopt-from-a-records-path) without hand-unwinding the index and minted id.

Nice to have in the same pass, or as follow-ups filed from it: plans, specs, and backlog
destinations (bullet dialect), using each tree's existing `new` planner.

## Acceptance

- `aw adopt .aw/inbox/x.prompt.md` previews `type: prompts`, destination
  `.aw/records/prompts/pending/<date>-<set>-NN-<id6>-<slug>.prompt.md`.
- `--apply` produces a file that `aw check prompts` passes, whose first line is the aw-prompt comment
  and whose remaining bytes equal the dropped file exactly; the inbox copy is removed.
- `aw adopt --type research` behavior is unchanged (regression tests).
- An unsupported type is still refused with a reason, never half-written.
- Module docstring, `--type` help, `.aw/inbox/README.md` ("Day-one support is the research tree"),
  and the installed inbox README template are updated to the new supported set.

## Why this blocks 2.0.0

The inbox and `aw adopt` are user-facing in 2.0.0. Shipping a drop zone whose only tooled exit
mis-files the commonest drop type, and whose correct path is hand-filing, contradicts the inbox's
own stated rule and produced real cleanup work in an adopter repo.
