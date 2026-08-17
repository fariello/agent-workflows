# .agents/docs/

Durable reference documentation, research notes, and narrative execution walkthroughs.

These are the STANDARD buckets. The list sets expectations; it does NOT limit what may live under `.agents/docs/` (other durable-doc content is allowed):

- **`research/`** - durable research, surveys, or analysis that an agent relied on for design or architecture decisions.
- **`walkthroughs/`** - narrative walkthroughs documenting the execution, validation, and verification details of implemented plans.
- **`specs/`** - design specifications and RFC-style documents (the `spec` workflow's home).
- **`prompts/`** - a historical/reference prompt LIBRARY, kept as origin material; not maintained in lockstep with the workflows and not the current spec. NOTE: this is the evergreen library, distinct from the sibling `.agents/prompts/` operational STAGING area (the run queue for run-once/research prompts), which also has a gitignored `.agents/prompts/local/` quarantine lane for raw/sensitive prompts like `/handoff` drafts (D94); a staged prompt's durable RESULTS land in `research/<topic>/` here. See `.agents/prompts/README.md`.
- **`roadmaps/`** - forward-looking roadmap and consideration documents.

Buckets follow the standard naming convention: `YYYYMMDD-HHMM-NN-<slug>.md` (local time). Walkthrough files end with `-walkthrough.md`. The `prompts/` bucket keeps its historical filenames.
