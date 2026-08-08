---
id: bv6n38
created: 20260808
set: attention-registry-cross-tree-status-and-whatnext
order: 00
topic: [attention-registry, status-model, whatnext, tooling]
model: 
kind: survey
status: active
outcome: none-yet
summary: Design survey for a cross-tree attention registry: standardized status vocabulary, deterministic aw attention scanner+writer, and whatnext-as-reader
consumed-by: []
---

# Survey: cross-tree attention registry (status model, deterministic scanner+writer, whatnext-as-reader)

Grounding research for a forthcoming functional and design spec. The problem: the repo has a mature,
machine-legible state model, but it is applied UNEVENLY across the `.agents/` artifact trees, and
`/whatnext` re-derives "what needs attention" at runtime by having the LLM read raw files, directories,
git, and TODO.md every time. That is expensive (many tokens), non-deterministic, and structurally blind
to trees it was never told to scan (specs, research, roadmaps, walkthroughs). This survey records the
measured landscape and the reusable primitives a cheap deterministic tool would stand on, so the spec
can be authored against evidence rather than assertion.

## 1. The measured asymmetry (which trees have machine-legible state)

| Tree | Directory disposition | Status field | Workflow history | Manifest/INDEX | /whatnext reads it |
| --- | --- | --- | --- | --- | --- |
| `.agents/plans/` | yes (pending/executed/superseded/not-executed/reusable) | yes (front-matter `- Status:` enum) | yes (`## Workflow history`) | yes (INDEX.json/.md + STATUS.md) | yes, directly |
| `.agents/prompts/` | yes (same lifecycle dirs) | yes (lifecycle) | via retire header | no | yes (pending only) |
| `.agents/comms/` | yes (inbox/sent/archive/acks) | yes (ack enum in header) | no | no | yes (headers only) |
| `.agents/docs/research/` | tiered (intake/active flat; reference/archive sharded) | yes (frontmatter `status:` enum, tool-owned) | no | yes (INDEX.json/.md) | NO |
| `.agents/docs/specs/` | NO (flat) | NO (free-form prose `- Status:` bullet) | NO | NO | NO |
| `.agents/docs/walkthroughs/` | NO | NO | no | NO | NO |
| `.agents/docs/roadmaps/` | NO | NO | no | NO | NO |

Source: read of each tree's README plus `.agents/workflows/whatnext/whatnext.md`. Specs are the worst
offender THAT MATTERS, because specs routinely describe unbuilt or deferred work (external-delivery,
clean-delta, pip/PyPI). Today a deferred spec is invisible to `/whatnext` unless a human transcribed it
into TODO.md, a pending plan, or a comms message. That "someone has to remember" bridge is exactly the
failure mode the registry removes.

## 2. How /whatnext works today (the cost problem)

`.agents/workflows/whatnext/whatnext.md` Step 1 ("Gather from every place lingering items live") is an
explicit closed list the LLM walks by reading raw sources each run:

- Plans board: prefers the deterministic `aw plans` scanner, else reads `.agents/plans/pending/*.md`
  front-matter (whatnext.md:49-56).
- Staged prompts: `ls .agents/prompts/pending/` (whatnext.md:57-58).
- Comms inbox headers (whatnext.md:59-61).
- TODO.md backlog (whatnext.md:62-63).
- DECISIONS.md + CHANGELOG.md tails (whatnext.md:64-65).
- Current session/chat (ephemeral, unverified) (whatnext.md:66-72).
- Catch-all "anything else that obviously holds pending work ... use judgment" (whatnext.md:73-74).

Observations: (a) it already REACHES for a deterministic scanner where one exists (`aw plans`), which is
the pattern to generalize; (b) everything else is raw file/dir reads by the model; (c) it never scans
specs/research/roadmaps/walkthroughs at all. The token cost scales with corpus size and is paid every
invocation, yet most of the answer is a pure function of on-disk state.

## 3. Reusable primitives that already exist (build-on, not build-anew)

`agent_workflows/artifact_core.py` already provides the scanner skeleton a cross-tree tool needs:

- `iter_scan_files(repo_root, scan_roots=SCAN_ROOTS)` (artifact_core.py:169): deterministic sorted walk
  of tracked-text files. `SCAN_ROOTS` already includes `.agents/plans` and `.agents/docs`
  (artifact_core.py:157-164), so specs/research/roadmaps/walkthroughs are already in the walk envelope.
- `Drift` NamedTuple + `render_agent_drift` (tab-separated `location\trule\tdetail`) +
  `drift_exit_code` (0 clean / 1 drift) (artifact_core.py:238-256): the EXACT machine-readable `--check`
  convention every existing area reuses. The registry's `--check` mode should reuse this verbatim.
- `find_dangling_citations(...)` (artifact_core.py:198): area-parameterized citation-rot detector.
- id6 primitives (`is_valid_id6`, `iter_id6_in_text`, `generate_id6`), `kebab`, shard math
  (`shard_for_date` -> `YYYYMM-Www`), `atomic_write`, `git_mv` (artifact_core.py:45-155): identity,
  safe writes, and tracked moves for the writer verbs.

Prior art for the registry OUTPUT: `agent_workflows/plans.py:219` already renders a grouped-by-status
`STATUS.md` board, and `plans_index.py`/`research_index.py` already emit `INDEX.json` + `INDEX.md` with a
`--check` drift gate. The registry is a cross-tree generalization of these, not a novel mechanism.

## 4. The status-vocabulary reconciliation problem (the hard design question)

The trees do NOT share a status vocabulary today:

- Plans (plans.py:25-27): pre-terminal `draft, to-review, reviewed, approved, auto-approved`; terminal
  `executed, superseded, not-executed`; standing `reusable`. Directory carries disposition; front-matter
  `- Status:` carries readiness (D52, D65).
- Research (research_contract.py:130): `intake, active, reference, archive` (a reference/archival
  lifecycle, tool-owned), with hot vs sharded split.
- Specs: free-form prose, observed ad hoc values `DRAFT`, `canonical`, `draft (evidence-gated)`,
  `approved`, `APPROVED ... Go`, and (newly, by hand) `Implemented`.

These vocabularies encode DIFFERENT lifecycles (an execution pipeline vs a reference lifecycle vs a design
lifecycle). The registry must NOT force one enum onto all of them. The promising abstraction is a small,
tree-agnostic ATTENTION CLASS derived from each tree's own status, e.g.:

- `needs-attention` (draft/to-review/reviewed/approved-not-yet-built, deferred-with-open-gate, intake)
- `in-flight` (active, approved-and-in-execution)
- `done` (executed, implemented, canonical, reference)
- `parked` (superseded, not-executed, archive, deferred-by-decision)

i.e. each tree keeps its native status enum; the registry defines a pure MAPPING from (tree, native
status) -> attention class. That preserves existing tooling and lets one scanner answer "what needs
attention" across every tree. A `deferred`/gated item should additionally cite WHY + the gating
TODO/decision so the registry can show the blocker.

## 5. Deployment facts that constrain the design

From the deployment map (importable package vs workflow tree):

- An `aw <verb>` must live in the importable package `agent_workflows/` (ships via the wheel;
  reachable as both `aw <verb>` and `python -m agent_workflows <verb>` in every install). The module
  pattern is one file per feature (`plans_index.py`, `research_index.py`, `ipd_lint.py`), each with a
  `run(args) -> int`, wired at two edit points in `cli.py` (`_build_parser` + `_dispatch`).
- Agent-run-in-target scripts (not `aw` verbs) live under a workflow's `tools/` dir, copied per-target.
  This is the WRONG home for the registry, which should be an importable `aw` verb.
- NAME COLLISION: `aw status` ALREADY EXISTS (cli.py:144, `_run_status`) and reports installer/version
  state. The new verb must be named distinctly; `aw attention` is the natural choice.
- The registry OUTPUT file belongs in the target's `.agents/` tree (like `.agents/plans/INDEX.json`),
  regenerated by the tool and committed, so `--check` can gate it in CI and `/whatnext` reads it cheaply.

## 6. Candidate design shape (for the spec to formalize)

- A shared, tree-agnostic ATTENTION-CLASS mapping (Section 4) layered over each tree's native status.
- A REQUIRED, standardized front-matter `Status:` (or tool-owned `status:`) on trees that lack one
  (specs first) plus a `## Workflow history` append convention lifted from plans.
- `aw attention` (READ): scans the standardized trees via `iter_scan_files`, reads front-matter,
  regenerates a committed `.agents/ATTENTION.md` + `.agents/ATTENTION.json` registry grouped by
  attention class, with a `--check` drift mode reusing `Drift`/`drift_exit_code` (CI-wireable), and a
  `--agent` machine-readable mode.
- `aw attention set <file> <status>` and `aw attention note <file> ...` (WRITE): validate the enum,
  rewrite the front-matter, append the dated `## Workflow history` line, and refresh the registry, all
  atomically (`atomic_write`) and self-recording. This is the "tool updates statuses and keeps history"
  capability requested.
- `/whatnext` rewired to READ the registry (a handful of tokens) and escalate to deep reading only for
  the specific flagged items, instead of scouring blindly.

Full-vision design; first build phase scoped to: standardize+require Status/history on specs, the
`aw attention` scanner + registry over the already-structured trees plus specs, and whatnext-as-reader.
Write verbs and walkthroughs/roadmaps adoption are named later phases.

## 7. Open questions the spec must resolve

- OQ1: exact attention-class enum and the per-tree (native status -> class) mapping table.
- OQ2: one unified `Status:` field name/format across trees, or keep each tree's native field and only
  standardize the MAPPING? (Leaning: keep native fields, standardize the mapping + require the field.)
- OQ3: one registry file at `.agents/ATTENTION.*`, or per-tree registries plus a roll-up? Token cost vs
  locality.
- OQ4: how a deferred/gated item expresses its gate (a `Blocked-by:`/`Gate:` field citing a TODO line or
  Dnn) so the registry can render the blocker and `/whatnext` can prioritize.
- OQ5: how `--check` wires to CI and whether the registry is required-in-sync (like INDEX `--check`) or
  advisory.
- OQ6: whether specs stay FLAT with a Status field (leaning yes; only 8 files, low churn) or adopt
  disposition subdirs (rejected candidate: breaks every existing `YYYYMMDD-HHMM-NN` citation path).
- OQ7: the write verbs' interaction with the existing per-tree tools (e.g. `aw plans` already owns plan
  status/history) - does `aw attention set` delegate to the owning tool, or is it read-only for
  tool-owned trees and write-only for the new ones (specs/roadmaps/walkthroughs)?

## 8. Outcome

Evidence gathered; ready to author the functional and design spec. The registry is a generalization of
existing, proven repo mechanisms (`aw plans`/`aw research` scanners, the `--check`/`Drift` convention,
`plans.py` STATUS.md), not new invention. The load-bearing design decision is the tree-agnostic attention
class + native-status mapping (Section 4 / OQ1-OQ2), which the spec will resolve and then send for
external model review (gpt-5.6 and Gemini) before any IPD Set.
