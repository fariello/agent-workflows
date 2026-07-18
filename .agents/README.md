# .agents/

Agent tooling for this repository.

- **`workflows/`** holds the installed agent-workflows framework (managed by `aw install`;
  do not hand-edit - changes are overwritten/pruned on the next install). See
  `workflows/index.md` for the catalog of workflows and how to run them.
- **`plans/`** holds YOUR Implementation Plan Documents (IPDs) through their lifecycle.
  See `plans/README.md`.
- **`docs/`** holds durable reference docs in buckets (research, walkthroughs, specs, prompts,
  roadmaps). See `docs/README.md`.
- **`prompts/`** holds run-once and research prompts QUEUED to run, through a plan-style lifecycle
  (`pending/` -> `executed/`, etc.). This is operational STAGING (the run queue), distinct from the
  evergreen `docs/prompts/` LIBRARY; a prompt's durable RESULTS are filed under `docs/research/<topic>/`.
  See `prompts/README.md`.
- **`comms/`** (once scaffolded by `aw install`) holds the inter-agent comms convention: a gitignored
  `local/` inbox lane and a tracked `shared/` lane for filesystem messages between agents. See
  `comms/README.md`.

You own `plans/`, `docs/`, `prompts/`, and `comms/`; the framework owns `workflows/`.
