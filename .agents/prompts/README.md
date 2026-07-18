# .agents/prompts/

Operational STAGING for run-once and research prompts that are QUEUED to be executed, organized by
lifecycle state. Prompt files are named `YYYYMMDD-HHMM-NN-<slug>.md` (the creating machine's local date
and time; `NN` is a two-digit per-minute sequence; `<slug>` is lowercase kebab-case), the same
convention as plans.

This is NOT the same as `.agents/docs/prompts/`. The two prompt homes are:

- **`.agents/prompts/`** (here): operational staging. "What prompt is queued to run?" A prompt lands
  in `pending/`, is run, and its lifecycle is tracked by MOVING it between the buckets below. Answer
  the question `ls .agents/prompts/pending/` with a glance.
- **`.agents/docs/prompts/`**: the evergreen, copy-paste prompt LIBRARY (reference material, not stamped
  with a framework version, not a run queue).

## The prompt -> results convention

A staged prompt produces RESULTS. Keep them apart:

- The PROMPT lives here (`.agents/prompts/<bucket>/`).
- Its RESULTS (the durable research/analysis you rely on) are filed under
  `.agents/docs/research/<topic>/` (see `.agents/docs/research/README.md`).

This separation follows the filesystem-encoded-state principle (GUIDING_PRINCIPLES P5, DECISIONS D91):
the prompt's lifecycle is glanceable from its directory; the results are durable, path-cited artifacts.

## The lifecycle

- **`pending/`** - queued to run, or being iterated on.
- **`executed/`** - the prompt has been run and its results filed (terminal; `done/` is an accepted alias).
- **`superseded/`** - replaced by a better/subsequent prompt; kept for the record.
- **`not-executed/`** - deliberately decided against, no replacement.
- **`reusable/`** - prompts meant to be re-run repeatedly (e.g. a recurring verification runbook); not a
  terminal state.

Retire a prompt by prepending a `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>` header and
`git mv`ing it to `superseded/` or `not-executed/`. Never silently delete a prompt; retiring preserves
the record and the reason.

## Tracked, not gitignored

`.agents/prompts/` is TRACKED and travels with the repo, like `.agents/plans/`. It is deliberately NOT
gitignored the way the inter-agent comms `local/` lane is: a queued or reusable prompt is durable state
that other agents and humans should see. The installer never writes a `.gitignore` for this area.
