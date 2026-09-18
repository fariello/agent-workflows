# .aw/records/

The durable, TRACKED records for this repository: the typed artifacts that carry decisions,
plans, and findings forward. These ARE committed, alongside the code they describe.

This is NOT run scratch. Run records, verification evidence, and session logs from a
workflow run go to `.aw/workflow-artifacts/<workflow>/<RUN_ID>/`, which is gitignored and
local to one machine; `records/reviews/` is NOT that place, and neither is any other tree
here. If you are looking for somewhere to put a run's working material, it is
`.aw/workflow-artifacts/`, and its own README explains why that tree stays untracked (D92:
run records carry absolute home paths and session detail, and git history is permanent).

## The typed trees

Each tree owns one artifact type, named by the uniform grammar
`YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`, and each has its own README with the details.

- **`plans/`** holds Implementation Plan Documents (`.ipd.md`) through their lifecycle
  buckets (`pending/`, `executed/`, `superseded/`, `not-executed/`, `reusable/`).
- **`specs/`** holds specifications (`.spec.md`): the contracts plans are reviewed against.
- **`backlog/`** holds lightweight backlog items (`.backlog.md`) by status.
- **`reviews/`** holds typed review findings (`.review.md`), so an unfixed High or Blocker
  finding is a fact tooling can read rather than prose in a transcript.
- **`research/`** holds immortalized research and reference material, with a manifest.
- **`walkthroughs/`** holds narrative `...-walkthrough.md` accounts of how something was done.
- **`releases/`** holds release records (`.release.md`) that `Blocks-Release` gates resolve to.
- **`roadmaps/`** holds longer-horizon direction documents.
- **`prompts/`** holds prompt artifacts through a lifecycle; **`prompt-library/`** holds the
  standalone reusable prompt library.
- **`comms/`** holds inter-agent messages.

Use the `aw` verbs to create and move these (`aw ipd`, `aw specs`, `aw backlog`, `aw research`,
`aw index`, `aw archive`); do not hand-name artifacts or hand-maintain an index.

## The exceptions, which are deliberate

A few paths under this tree are NOT committed, and every one of them is named in the
framework-owned `.aw/.gitignore` rather than left to convention. Verify any of them with
`git check-ignore -v <path>`:

- `records/*/untracked/` lanes (for example `comms/untracked/`, `prompts/untracked/`) are
  box-local quarantine: a human promotes a reviewed copy into a tracked bucket with `git mv`.
- `records/history.jsonl` is a local activity log appended on every `aw` status write.
- `records/runs/` is the IPD driver's per-run durable state.
- `records/plans/INDEX.*` and `records/research/INDEX.*` are GENERATED views; regenerate with
  `aw index plans` / `aw index research`.

Everything else here is meant to be committed. If a tree looks like scratch to you, check
its README before moving anything: the mistake this front door exists to prevent is treating
a tracked typed tree as a place to dump run output.
