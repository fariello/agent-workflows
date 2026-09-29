# .agents/

Agent tooling for this repository.

- **`workflows/`** holds the installed agent-workflows framework (managed by `aw install`; do not hand-edit; changes are overwritten or pruned on the next install). See `workflows/index.md` for the catalog of workflows and how to run them.
- **`plans/`** holds YOUR Implementation Plan Documents (IPDs) through their lifecycle. See `plans/README.md`.
- **`prompts/`** holds staged reusable prompt definitions. See `prompts/README.md`.
- **`comms/`** holds inter-agent communication channels and inboxes. See `comms/README.md`.
- **`backlog/`** holds lightweight work tracking and triage.
- **`docs/`** holds reference documentation and specifications. See `docs/README.md`.
  - `docs/specs/`: specifications and design contracts. See `docs/specs/README.md`.
  - `docs/research/`: reference research, explorations, and benchmarks. See `docs/research/README.md`.
  - `docs/walkthroughs/`: narrative end-to-end walkthroughs. See `docs/walkthroughs/README.md`.
  - `docs/prompts/`: permanent prompt catalog. See `docs/prompts/README.md`.
  - `docs/roadmaps/`: long-range goals and milestones.

You own `plans/` and record trees; the framework owns `workflows/`.
