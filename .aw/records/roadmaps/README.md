# .aw/records/roadmaps/

Forward-looking roadmaps and "for consideration" direction documents: longer-horizon plans,
option surveys, and sequencing sketches that are broader than a single IPD and are not yet
committed work.

Named `YYYYMMDD-HHMM-NN-<slug>.md` (local time).

A roadmap records intent and possibilities, not a commitment to execute. When a roadmap item is
actually taken up, it becomes one or more IPDs under `.aw/records/plans/`; the roadmap remains as the
context and rationale. Note: `roadmaps` is a recognized `.aw/records/` bucket but is NOT scaffolded
by the installer's `DOCS_SUBDIRS` (that omission is deliberate per DECISIONS D73; the standard-bucket
list does not limit what may live under `.aw/records/`).

## Attention contract and Phase 3 admission verdict

Roadmaps remain excluded from `aw attention` (`tracked=False`).

The implemented attention spec (`20260808-1945-01`) Phase 3 requires four criteria for admission into the tracked attention view:
1. A real owner verb
2. A closed native status contract
3. A history contract
4. An exhaustive mapping from native status to attention class

The roadmaps tree fails three measured criteria:
- No owner verb: no `aw roadmaps` command exists to own writes or manage lifecycle transitions.
- No closed native status contract: the single roadmap artifact carries `- **Status:** DRAFT FOR CONSIDERATION`, a prose value inside bold markup that the contract parser (`SPEC_STATUS_RE`, which requires a bare single token) cannot parse.
- No history contract: 0 of 1 roadmap files carry a `## Workflow history` heading (and 0 of 1 mention the phrase in substring search).

The fourth criterion (an exhaustive mapping) fails as a direct consequence of having no closed native status contract to map over.

Because roadmaps are excluded from the attention board, running `aw attention <id6>` for a roadmap artifact does not fail as a missing artifact or typo. Instead, `aw attention` identifies that the selector resolves to an artifact in an excluded tree, reports the exclusion reason, and points the operator to `aw find <id6>` to view the artifact.
