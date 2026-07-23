# IPD (DRAFT STUB): external / out-of-repo install and native-skills delivery (research-spec first)

- Date: 2026-07-23
- Concern: reduce per-repo "pollution" and recurring token cost by delivering agent-workflows capability from outside the repo and/or via host-native portable skills, where hosts actually support it
- Scope (intended): decide, from evidence, how much of agent-workflows can live OUTSIDE a given repo (e.g. the pip-packaged data, a home-dir location, or host-native `.agents/skills/`) and still be discovered/followed by each host; then spec the delivery model. Starts as research/spec, not a build. Details TBD.
- Status: draft
- Set: install-safety-and-ownership
- Order: 4
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

> DRAFT STUB - PRELIMINARY. Captures INTENT and OBJECTIVES only. NOT ready for /plan-review or
> execution. This is RESEARCH/SPEC-FIRST: the central assumption (that a given host will resolve
> and follow agent-workflows content that lives OUTSIDE the repo) is UNPROVEN per host and
> LIKELY NEEDS MORE DISCUSSION. Do not execute as a build.

## Workflow history

- 2026-07-23 created as a draft stub (opencode its_direct/pt3-claude-opus-4.8-1m-us): the maintainer's original "Item 2" (workflows in ~/.local/agent-workflows so repos are not polluted), reframed after the two research docs (`.agents/docs/research/20260722-2241-...` and `...20260722-2317-...`) as research/spec-first. Preliminary.

## Intent and objectives

The maintainer's goal: not every repo should have to carry the full `.agents/workflows/` tree (and pay its footprint) to use agent-workflows fully; ideally AGENTS.md could point at an out-of-repo location, and the toolkit could lean on host-native portable mechanisms. The research already establishes the key realities this IPD must respect:

- The HOST application, not the model, decides file discovery; behavior varies per host and per host version.
- The pip package ALREADY ships the workflow tree as importable data (`agent_workflows/_data/.agents/workflows/`), so an out-of-repo SOURCE exists.
- `.agents/skills/<name>/SKILL.md` is a portable path that Codex, OpenCode, and GitHub Copilot natively discover; other content under `.agents/` is not automatically understood.
- Always-on behavioral directives are only reliable if the host loads them; a passive out-of-repo pointer may not be followed, whereas an action-bound trigger (see the interactive-questions work) is more reliable.
- Every in-repo reference today (shim bodies `Read and execute @.agents/workflows/...`, the AGENTS block, VERSION detection, integrity checks) assumes an in-repo copy.

The objective is to determine, per host, what can safely and reliably live outside the repo (packaged data path, home-dir, or host-native skills) versus what must remain in-repo, and to SPEC a delivery model that minimizes per-repo footprint without breaking discovery, versioning, or the ownership model.

## Objectives / must-haves (intent, not implementation)

- Evidence-first: prove (or probe) per host whether out-of-repo / skills-based delivery is discovered AND followed, before building.
- Do not reduce capability or reliability for hosts that need in-repo content; degrade to the current in-repo model where external delivery is unproven.
- Coordinate with the ownership/manifest model (IPD A): whatever is installed where must still be identifiable, versioned, and removable.
- Prefer host-native portable skills (`.agents/skills/`) where documented; keep a universal in-repo fallback.
- Keep the token-economy goal in view (research 2317): out-of-repo bodies + short triggers, not inlined trees.

## Known open questions / needs discussion (NON-EXHAUSTIVE)

- Per host: does an out-of-repo or home-dir instruction/workflow reference actually get resolved and followed? (Needs a probe/spec, not an assumption.)
- Which existing workflows are true SKILLS vs manual workflows vs agents/assessors (do not mechanically convert every `.md` to `SKILL.md`).
- How VERSION detection, integrity/drift, and the manifest work when content is not in-repo.
- Home-dir install ownership problem: a repo installer should not mutate a user's global agent config without clear consent (research: Hermes/Codex user-scope caveats).
- How the AGENTS.md pointer/trigger references an external location portably across hosts.
- Whether this is one IPD or splits into (research/probe spec) + (per-tier build) IPDs.

## Dependencies

- Coordinates with the ownership/manifest model (IPD A) and the interactive-questions trigger pattern (IPD D). Independent enough to research in parallel, but any BUILD should follow A so external artifacts are still manifest-tracked. Sequenced after A/B in the believed order, but the research half can start anytime.

## Approval and execution gate

DRAFT STUB, research/spec-first. Must be fleshed out (starting with the per-host probe/spec), then any build IPD passes /plan-review + explicit human approval. Standard execution contract applies when fleshed out. Do NOT build out-of-repo delivery before the per-host resolve-and-follow assumption is verified.
