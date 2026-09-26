# Spec: Artifact metadata store: id+status front matter, per-artifact event logs, SQLite cache

- Date: 2026-09-25
- Status: reviewed
- Blocks-Release: next
- Id: 4sd62s
- Author: aw specs new
- Scope: Move all aw artifact metadata and history into tracked per-artifact JSONL event logs at .aw/records/meta/<id6>.jsonl; compact front matter (id, status); gitignored SQLite index replaces INDEX.* and STATUS.md; hard cutover via aw migrate metadata
- Work-Kind: feature
- Relation to prior work: AMENDS approved spec `2vev8j` (artifact metadata storage). Keeps its seq ordering (4.3), UTC rule (4.4), SQLite-as-cache rule (4.6), legacy import rule (4.7), and backward-edge ruling (4.8). REPLACES its C4 (current state inline), 4.5 (one inline history line), C8 (incremental migration) and AC-11 (partially migrated corpus valid), and resolves its OQ-2 (backlog/specs migrate too) and OQ-3 (flat path).

## 1. Problem statement

Artifact metadata today is a hand-editable `- Field: value` bullet block plus an unbounded
`## Workflow history` section in every Markdown artifact. Measured at HEAD `83b14a5f` on 2026-09-25
and RE-MEASURED at review (HEAD `44df26b3`, same day), with the review's values shown where they
differ (re-derive at implementation time; these drift daily):

| Fact | Value |
|---|---|
| Package modules reading or writing bullet metadata | 35 of 170 at authoring; 37 of 174 at review (a coarse `rg` for the bullet patterns) |
| Independent generic key/value parsers | ~9 (`ipd_schema.parse_metadata_block`, `runner_shared._front_matter_bullets`, `status_set` finditer, `plan_readiness._OQ_FIELD_RE`, `backlog.parse_item`, `specs` line readers, `research_contract.parse_frontmatter` (YAML), `comms.parse_envelope_header`, `prompts` comment parser) |
| Copies of `Id`/`Status`/`Set` regexes | 50+, with inconsistent whitespace (`^- `, `^-\s*`, `^-[ \t]*`) and capture (`\S+` vs `.+?`) rules. A live consequence, fixed 2026-09-25 in `44df26b3`: `attention._plans_id` searched a 2048-char prefix with an unanchored `(\S+)` and rendered plan `je74a0` as `je7` on the board |
| Modules referencing `## Workflow history` | 23 at review (the authoring figure of ~13 undercounted), with four incompatible orderings (see `2vev8j` section 1) |
| Readers that DISAGREE on the same corpus | `selectors` vs `plans_index`: 24 plans (the `_STATUS_RE` PARITY note in `selectors.py`) |
| Distinct pre-`##` field names in use | 57 |
| Tracked `.md` records under `.aw/records/` | 1969 at review; 1411 carry `## Workflow history`; 549 carry no `- Id:` BULLET, but only 64 lifecycle records carry no id6 in ANY form (bullet, YAML `id:`, or prompt comment), and 339 of the 549 are review records, which BY DESIGN carry no id of their own (see 4.1a) |
| Generated index files | 4 gitignored `INDEX.{json,md}` (plans, research) plus committed `plans/STATUS.md`, stale since 2026-08-17 |
| INDEX churn before untracking | 14 of 328 commits in 14 days only fixed INDEX drift (backlog `ila6vl`) |

Consequences:

- P1 Duplication. Every consumer re-derives metadata with its own regex, so behavior differs by
  consumer, and a fix in one reader does not reach the others.
- P2 Forgeable attestations. `Readiness`, `Approval`, and `Status` are prose that any editor can
  write; AGENTS.md devotes a section to forbidding it, and lint (`IPD-M107`) and hooks
  (`status_untooled_gate`) exist only to detect it after the fact.
- P3 History is unordered and partly lost (`2vev8j` E1-E4): prepend vs append vs replace, and the
  only full backlog/spec log is gitignored.
- P4 Context cost. Every agent read of an artifact pays for ~16 metadata bullets and an
  append-forever history that is almost never relevant to the task.
- P5 Query cost. `aw find`, `aw attention`, and `aw ipd board` re-read the entire corpus per call,
  twice in places (backlog `59t9x5`: 1509 opens for 754 plans; `8cpbia`: 54x redundant walks).

## 2. Evidence and options considered

The maintainer asked for the optimal solution across cost, maintainability, and UX, noting adoption
is effectively zero and nothing has shipped since 1.2.0 (`v1.3.0-rc.1..HEAD` was 4050 commits at
authoring and 4125 at review), so a
breaking change costs the community almost nothing. `CHANGELOG.md` already carries `2.0.0 (pending)`.

Storage options, evaluated against this repo's execution model (isolated git worktree per execute
item, merge back through `runner_shared.integrate_lane_branch`):

| Option | Verdict | Reason |
|---|---|---|
| O1 SQLite as the tracked authority | REJECTED | Binary; every parallel lane finalize conflicts on merge; no diff/review visibility; breaks the code paths that compare HEAD vs staged status (at least `check_engine._status_meta`, `hooks/executed_transition_gate.py`, `hooks/status_untooled_gate.py`, `hooks/ipd_dependency_statement_gate.py`, `artifact_audit.FinalizeEvidenceIndex`, and the `ipd_lifecycle` finalize lookups; see 4.4 for why the list is a floor). A SQLite merge driver is local-only and not cloned. |
| O2 SQLite gitignored as the ONLY store (incl. history) | REJECTED | Fresh clone, CI, second machine, or collaborator gets no metadata. This is exactly the data loss `2vev8j` E4 measured (176 of 177 sidecar records exist only on one machine). IPD-S405 and finalize evidence gates would fail on any checkout without the DB. |
| O3 History derived from `git log` + commit trailers, SQLite indexes it | REJECTED | Squash merges and rebases destroy intermediate transitions; shallow clones, sdists, tarballs lose history; a hand edit plus raw commit silently skips an event; needs a trailer convention enforced everywhere. |
| O4 Per-artifact state snapshot `<id6>.json` + history array | REJECTED | Stores state and history side by side, so they can disagree, requiring an intra-file drift check on top of front-matter drift. Multi-line diffs per change. |
| O5 Per-artifact append-only event log `<id6>.jsonl`, state = replay, SQLite as disposable cache | CHOSEN | Tracked, survives clone/squash/tarball; path is a pure function of the immutable id6 so renames and moves never touch it; different artifacts never contend (satisfies `2vev8j` C3); one appended line per change; ordering by explicit `seq`; state cannot contradict history because it is derived from it. Already the design `2vev8j` 4.2-4.3 approved for history. |

Front-matter options:

| Option | Verdict | Reason |
|---|---|---|
| F1 `id` only | REJECTED | Loses at-a-glance status on GitHub, in raw file views, and in `.md` diffs. |
| F2 `id` + `status` | CHOSEN (maintainer, 2026-09-25) | Status is the one field humans scan for; cost is one cached field kept honest by a drift check. |
| F3 All current fields as YAML | REJECTED | Not compact; reintroduces P1/P2. |

## 3. Criteria

- C1 `[Must]` ONE authority for every aw-owned metadata field and all history: the per-artifact event
  log. No other surface (front matter, filename, SQLite, directory) is authoritative except where
  section 4.6 names a deliberate, checked mirror.
- C2 `[Must]` A fresh clone (including `--depth 1`) carries all current metadata and full history.
- C3 `[Must]` Two lanes changing DIFFERENT artifacts never write the same tracked file.
- C4 `[Must]` Ordering is explicit (`seq`), never inferred from line position, dates, or commits
  (inherits `2vev8j` C1).
- C5 `[Must]` Exactly ONE read/write API (`artifact_meta`) for metadata; no module outside it parses
  front matter or event logs.
- C6 `[Must]` A refused or `--dry-run` change writes no event; a failed event write fails the change
  (inherits `2vev8j` C5).
- C7 `[Must]` A status change remains visible in a review diff (front-matter `status` line and one
  appended event line).
- C8 `[Constraint]` No new runtime dependency. `sqlite3` and `json` are stdlib; `filelock` is present.
- C9 `[Constraint]` Hard cutover: after migration the toolkit reads ONE format. No dual-format
  readers (maintainer, 2026-09-25).
- C10 `[Constraint]` Filename-encoded metadata (date, setid, NN order, id6, slug, type facet) is
  UNCHANGED (maintainer, 2026-09-25). The filename remains a checked mirror of `set`/`order`.
- C11 `[Want]` Measurably lower agent context per artifact read and faster `aw find`/`attention`/board.

## 3a. Non-goals

- N1 NOT a change to the artifact-naming grammar or the directory lifecycle (`pending/` ->
  `executed/` etc.). Directories still carry disposition.
- N2 NOT a change to status vocabularies or the lifecycle transition table (beyond what `2vev8j` 4.8
  already decided).
- N3 NOT a move of prose. Body sections (execution/validation checklists, open questions, E/V items)
  stay in Markdown. Only aw-owned metadata FIELDS and history move.
- N4 NOT a change to comms envelopes, run records (`.aw/records/runs/`), or run analytics.
- N5 NOT a dual-format transition period (C9).

## 3b. Acceptance criteria

| ID | Covers | Criterion | Evidence that satisfies it |
|---|---|---|---|
| AC-1 | C1, C5 | No module outside `artifact_meta` reads or writes front matter, bullet metadata, `## Workflow history`, or `meta/*.jsonl`. | A pasted `rg` over `agent_workflows/` for the legacy bullet/heading patterns and for `records/meta` returning hits ONLY in `artifact_meta.py` and `migrate_metadata.py`; plus a test enforcing it. |
| AC-2 | C2 | A `git clone --depth 1` yields full state and history. | Clone to a temp dir, run `aw show <id6> --history` on a migrated plan with a multi-event history, paste output. |
| AC-3 | C3 | Two branches transitioning different artifacts merge cleanly. | Two-branch merge test, pasted. |
| AC-4 | C4 | Read order is independent of line order on disk. | Test shuffling a log's lines and asserting `seq`-ordered replay is unchanged; test rejecting a gapped or duplicate `seq`. |
| AC-5 | C6 | Refused and dry-run transitions leave the log byte-identical; a forced write failure leaves status unchanged. | Tests, pasted. |
| AC-6 | C7 | A status transition diff shows the front-matter `status` line and one added log line. | `git diff` of a real transition, pasted. |
| AC-7 | 4.6 | Every mirror (front-matter `status`, filename `set`/`order`/`id`, disposition directory) is checked against the log. | `aw check meta` detects each drift kind in a fixture, output pasted; zero findings on the migrated corpus, pasted. |
| AC-8 | 4.5 | The SQLite cache is disposable: deleting it changes no command output. | Run `aw find`/`aw attention --format json` with and without `.aw/state/index.db`, diff empty, pasted. |
| AC-9 | 4.5, C11 | INDEX.* and STATUS.md are gone and nothing regenerates them. | `git ls-files` and filesystem check, pasted; `rg` for `INDEX.json`/`STATUS.md` in `agent_workflows/` returns only the migrator's cleanup. |
| AC-10 | 5 | Migration is idempotent, journaled, dry-run by default, and loses no information. | Run on a copy of this repo: dry-run report; apply; second apply is a no-op; every legacy field value and every raw legacy history line is present in the logs (automated round-trip check), pasted. |
| AC-11 | C9 | An unmigrated repo is refused by every metadata-reading command with a message naming `aw migrate metadata`. | Test, pasted. |
| AC-12 | C8 | `pyproject.toml` `dependencies` unchanged. | Pasted. |
| AC-13 | C11 | Measured before/after: bytes per plan read by an agent, and warm/cold end-to-end `aw find` and `aw attention`. | Numbers pasted, measured per the AGENTS.md end-to-end rule. No target asserted. |
| AC-14 | 4.1a | A review record has no log of its own; each review round is ONE `op: review` event in its SUBJECT's log, and the file's round count equals the subject's review-event count. | `rg` showing no `meta/*.jsonl` is created for a review; a test that runs a review and asserts exactly one `review` event is appended to the subject's log; `aw check meta` detecting a round-count mismatch in a fixture, pasted. |
| AC-15 | 4.4 | `readiness` (plans) is refused unless the same append carries an `op: review` event for that subject in the same transaction. | A test in which a bare `set readiness=go` is refused and the same write accompanied by a review event succeeds, pasted. |
| AC-16 | 5.2 | The migration's one commit may rewrite terminal-directory artifacts, and ONLY the migration may. | The migration commit passes the executed-plan hook with no `--no-verify`; a separate raw edit to an executed plan after cutover is still refused by it, both pasted. |
| AC-17 | C3, 4.7 | Two lanes changing the SAME artifact produce a detected, non-silent conflict, and nothing merges a duplicated `seq`. | A two-branch test on one artifact asserting the merge does not produce a valid log with duplicate `seq` (it conflicts or `aw check meta` fails), pasted. |
| AC-18 | 4.5 | With a non-`repository` records backend (companion/home), logs live beside the records they describe and the cache still resolves. | A companion-backend fixture showing `meta/<id6>.jsonl` under the resolved records root and `aw find` working, pasted. |

## 3c. Honest limits

- The blast-radius counts are from one inventory pass; re-measure at planning time.
- Two lanes changing the SAME artifact still conflict at the end of its log. This is judged rare
  (lanes own distinct plans) and is surfaced loudly, not auto-resolved (4.7).
- Moving attestations into tool-written events makes forgery HARDER, not impossible: a party with
  write access can still append a line by hand. Hooks and `aw check` detect malformed or untooled
  events; neither is an enforcement boundary (same honesty as the integration lock).
- Front-matter `status` is a cache that can drift under hand edits; it is detected, not prevented.
- Token savings (C11) are directional until AC-13 measures them.
- C2 holds for the RECORDS, not for machine-local context. `aw attention` also surfaces stranded
  lanes and run state, which live in gitignored `.aw/records/runs/` and worktrees; a fresh clone has
  none of that, before and after this spec. Do not read C2 as "a clone sees everything a machine
  sees".
- The review verdict becomes tool-written (4.1a), but the findings and decisions TABLES stay prose in
  the review file. A hand edit that changes a severity or a decision is still possible and is caught
  only by the existing `review_findings` parse and gating rules, not by the log.
- The migration rewrites every terminal artifact once (5.2 step 4a). That single commit is a
  deliberate, one-time exception to the rule that executed plans are never re-committed, and it
  makes `git blame` on those files point at the migration. The history itself is preserved in the
  logs; line-level blame on the old bullet blocks is not.

## 4. Design

### 4.1 Artifact file shape

```
---
id: abc123
status: approved
---
<!-- aw-managed: metadata lives in .aw/records/meta/<id>.jsonl; use `aw show <id>`; agents read .aw/AGENT_QUICKSTART.md -->
# <Title>
...body...
```

- YAML-delimited, exactly two keys, fixed order. Parsed by `artifact_meta` with a strict line
  grammar, not a YAML library (C8; no ambiguity).
- The banner is ONE HTML comment, not the proposed `# START README FIRST` H1 block. Reason: an H1
  renders as a large heading on GitHub, collides with the "first H1 is the title" rule in
  `ipd_schema` section-order checks, and ~80 tokens across ~2000 files is a real recurring cost. The
  comment is invisible when rendered and still read by agents. Its exact text is a template owned by
  `artifact_meta` and checked for presence.
- `.aw/AGENT_QUICKSTART.md` and `.aw/QUICKSTART.md` are created by the installer (they do not exist
  today).
- No `## Workflow history` section. `aw show <id6> --history` renders it.
- Artifacts that are not aw-lifecycle records (walkthroughs, research reference packages, comms
  messages) get front matter only if they carry an id today; this is settled per type in the plan.

### 4.1a Review records are events in their SUBJECT's log

MAINTAINER DECISION, 2026-09-25, made during spec review (finding SR-001).

THE PROBLEM IT SETTLES: a review record's filename id6 is the REVIEWED artifact's id6, by deliberate
design (`.aw/records/reviews/README.md`, "Naming": "`<id6>` is the REVIEWED ARTIFACT's id6, not a fresh
identifier"), so it survives renames. Measured at review: all 338 review records reuse their
subject's id6 and none carries an id of its own. Under 4.2's path rule a review and its subject would
therefore claim the SAME `meta/<id6>.jsonl`, and the second writer would corrupt or refuse the
first's history. The authored spec did not address this, while its 4.2 field list named
`subject-id/type (reviews)`, implying reviews get a log.

THE DECISION: a review has NO log and NO id of its own. Each review ROUND is recorded as ONE event
in the SUBJECT's log. A review is metadata about its subject, and this is where the spec already
needs it: 4.4 makes `readiness` settable only by a review event, which requires the review to be an
event in the subject's log.

WHAT FOLLOWS:

1. A new event `op: review` (added to 4.2's op list) carrying `round` (int, matching the file's
   `## Round <n>`), `verdict` (one of `plan_readiness.VERDICTS`), `reviewer`, and, for a plan,
   `readiness`. The verdict becomes tool-written; today it is a hand-editable `- Verdict:` line.
2. The review FILE keeps its findings and decisions TABLES as readable prose (N3), unchanged in shape
   and still parsed by `review_findings`. Its front matter is `subject: <id6>` and `subject_type:
   <ipd|spec>`, NOT `id:`, so no tool can mistake it for an artifact with its own log.
3. `aw check meta` (4.6) treats a review file as a DEPENDENT of its subject rather than an orphan, and
   adds one drift rule: the file's round count must equal the number of `review` events in the
   subject's log.
4. `review_findings.subject_gating_blocks` keeps reading the current round's findings from the FILE;
   only the verdict and readiness move to the log.

ALTERNATIVES REJECTED: (a) no log for reviews, fields stay in the file, rejected because it leaves
the verdict forgeable, which is P2, the problem this spec exists to fix; (b) mint an id6 per review
and link via a separate field, rejected because it renames all 338 records and reverses the
deliberate link-by-subject design for no benefit the subject log does not already give.

IRREVERSIBILITY: it fixes the review record's front-matter shape and a new event type in a tracked
format that every later review writes. Reversing it later means rewriting every review event.

### 4.2 Event log: `.aw/records/meta/<id6>.jsonl`

- Tracked. Flat directory (resolves `2vev8j` OQ-3; ~2000 files is fine for git and filesystems;
  sharding is a later reversible change).
- One JSON object per line, UTF-8, sorted keys, no trailing whitespace, LF-terminated.
- Event schema (v1):
  - `v`: schema version (int)
  - `seq`: contiguous int per artifact. `0` is the migration checkpoint for migrated artifacts; `1`
    is creation for artifacts born under this spec (inherits `2vev8j` 4.3).
  - `at`: RFC 3339 UTC timestamp, display only (inherits `2vev8j` 4.4).
  - `actor`: tool and host/model identity string (no machine paths, usernames, or hostnames; the
    leak sanitizer rules apply).
  - `op`: one of `create`, `set`, `unset`, `transition`, `note`, `checkpoint`, `legacy`, `review`
    (4.1a).
  - `fields`: object of field -> new value for `create`/`set`/`checkpoint`; list of names for `unset`.
  - `from`/`to`: for `transition` (status), validated against that TYPE's lifecycle table. Not every
    type has an enforced table today (specs have `attention_contract.SPEC_TRANSITIONS`, plans the
    `ipd_lifecycle` ranks plus `2vev8j` 4.8; backlog, research, prompts, and releases validate the
    target VALUE only). A type with no table validates the value only, exactly as today; this spec
    does not invent tables (N2).
  - `by_human`: bool, only on events the setter records via `--by-human`.
  - `message`: optional free text.
  - `legacy`: for `op: legacy`, the verbatim original line, observed day, original ordinal, and
    `ordering_confidence` (`known` / `inferred-from-git` / `unknown`) per `2vev8j` 4.7.
- Current state = fold of events in `seq` order. The log carries EVERY aw-owned field: type, set,
  order, kind, priority, work-kind, blocks-release, readiness, approval, from-backlog, from-spec,
  graduated-to, item-dependencies, gate-kind/ref/summary, version (releases), etc. Review records
  carry no log (4.1a). The exact per-type field registry is a table in `artifact_meta`, and unknown
  fields are refused.
- Prose-valued fields (`Summary`, `Scope`, `Concern`, `Motivation`, `Relation to prior work`) move
  into BODY sections at migration, not into the log (N3). `title` stays the H1.

### 4.3 The single API: `agent_workflows/artifact_meta.py`

- `read(id6) -> State`, `history(id6) -> list[Event]`, `append(id6, events, *, expect_seq)`,
  `create(...)`, `resolve(path|id6)`.
- Writes take a per-artifact `filelock`, verify `expect_seq` (optimistic concurrency), write via
  temp file + `fsync` + atomic replace of the whole log (logs are small), then rewrite the
  front-matter `status` mirror in the same transaction. Either both change or neither does (C6).
- Validation on read: fail closed on malformed JSON, gapped/duplicate `seq`, unknown `op` or field,
  id mismatch with the artifact, or a status transition not in the lifecycle table.
- All ~9 parsers and the 50+ ad-hoc regexes are deleted and their callers routed here. The
  `selectors` vs `plans_index` 24-record disagreement is resolved by construction: there is one
  reader. The plan must record which behavior each disagreeing consumer loses.

### 4.4 Consumers that change behavior (not just port)

- `IPD-S405` and every gate reading history query `artifact_meta.history`, never Markdown (inherits
  `2vev8j` 5).
- `attention_contract.last_history_at` = `at` of the highest-`seq` event (fixes `2vev8j` E3).
- The HEAD-vs-staged code paths (`check_engine._status_meta`, `hooks/executed_transition_gate.py`,
  `hooks/status_untooled_gate.py`, `hooks/ipd_dependency_statement_gate.py`, `artifact_audit`,
  `ipd_lifecycle` finalize lookups) compare the staged vs HEAD `meta/<id6>.jsonl` (new events
  appended) instead of `- Status:` lines. THIS LIST IS A FLOOR, NOT AN INVENTORY: the authored "6
  paths" omitted `ipd_dependency_statement_gate`, and a coarse `rg` for HEAD/staged reads also hits
  `runner_shared`, `work_cmd`, and `cli`. Plan step 5 MUST re-derive the full set by searching for
  `git show HEAD:`, `--cached`, and index reads of `.aw/records/`, and record each consumer's
  disposition. The
  "status changed without a matching history line" rule becomes "front-matter `status` differs
  from log replay" (a drift) or "log gained an event not produced by a tool" (untooled).
- `runner_shared._body_change_is_history_insert_only` and similar finalize scope logic treat
  `meta/<id6>.jsonl` for the plan being finalized as an owned path.
- `IPD-M107` (unattested Readiness) is replaced by: `readiness` can only be written in the same
  append as an `op: review` event for that subject (4.1a); the setter refuses otherwise (AC-15).
  `plan-review` and `spec-review` are agent workflows, not `aw` verbs, so the review workflow's
  instructions change from "write `- Readiness:` into the plan" (`plan-review.md`, "Write the
  structured `Readiness` field") to a tooled review-recording command that appends the event. Name
  that command in plan step 4. `aw ipd recheck-readiness` likewise appends a `review` event rather
  than editing a field.
- Scanners that walk `.aw/records/` (`selectors`, `artifact_refs`, `attention_contract`,
  `ipd_lint`, `specs`, `releases`, `artifact_core.iter_scan_files`) exclude `records/meta/` through
  ONE shared exclusion list in `artifact_core`.

### 4.5 SQLite cache: `.aw/state/index.db`

- Gitignored (under the existing `/state/` rule in `.aw/.gitignore`). Stdlib `sqlite3`, WAL mode.
- Resolved through the project-context authority (`project_context.resolve_project_context`, the
  way `runner_shared.state_root` resolves run state), NOT by assuming `<repo>/.aw/`. A repository
  whose `records_backend` is `companion` or `home` keeps its records, and therefore its
  `meta/*.jsonl` logs, OUTSIDE the repo; the logs always live under the RESOLVED records root, beside
  the records they describe (AC-18). Where lane worktrees share one cache, rows are keyed by worktree
  root (located with `git rev-parse --git-common-dir`), so a lane never reads another tree's state as
  its own.
- Tables: `artifacts(id6, worktree, path, type, bucket, status, set, order, ...)`, `events(id6, seq,
  ...)`, `files(path, size, mtime_ns, blob_sha)`. Refresh is incremental: re-read a log or artifact
  only when size/mtime_ns change, with a blob-sha tiebreak to close the same-tick mtime gap measured
  in backlog `8mkt5l`.
- Schema version row; a mismatch drops and rebuilds. Any open/corruption error drops and rebuilds.
  A command must never fail because the cache is missing or broken (AC-8).
- Replaces: `plans/INDEX.{json,md}`, `research/INDEX.{json,md}`, `plans/STATUS.md`, the
  `artifact_audit._INDEX_CACHE`, and the whole-corpus rescans in `aw find`, `aw attention`,
  `aw ipd board`. `aw index <type>` becomes `aw index rebuild`; `--check` drift checks for INDEX files
  are deleted along with `check.stale-index-*`.

### 4.6 Mirrors and drift (`aw check meta`)

The log is the authority. These are deliberate mirrors, each checked, each repairable with
`aw meta repair --apply`:

| Mirror | Reason it exists | Drift rule |
|---|---|---|
| Front-matter `status` | Human visibility (F2) | Must equal replayed status |
| Front-matter `id` | Links file to log | Must equal filename id6 and log identity |
| Filename `setid`, `NN`, `id6`, date | C10 | Must equal replayed `set`/`order`/`id`; date must equal `create.at` day |
| Disposition directory | N1 | Must be consistent with replayed status per type |
| Orphans | | A log with no artifact, or an artifact with no log, is an error. A review file is a DEPENDENT of its subject, never an orphan (4.1a) |
| Review rounds | 4.1a | A review file's `## Round <n>` count must equal the `review` events in its subject's log |

### 4.7 Concurrency and merges

- Different artifacts: disjoint files, clean merges (C3).
- Same artifact on two branches: both sides append after the same `seq`, giving a git conflict at
  the log tail (AC-17). The same collision also hits the front-matter `status` mirror, since both
  sides rewrite that line. NOT resolved with `merge=union` (it would silently duplicate `seq`). The runner's
  existing conflict path preserves the lane; `aw meta repair <id6>` offers a re-sequence of the
  losing side's events onto the winner, re-validated against the transition table, human-confirmed.

### 4.8 Tooled writes only

- Every metadata change goes through `aw set`, `aw specs set`, `aw backlog set`, `aw ipd ...`,
  `aw group`, `aw rename`, finalize, retirement. These already exist; they are re-pointed at
  `artifact_meta`.
- EXTEND the existing `aw show` (today `aw show <action_ref>` prints a record's full content and has
  no `--history`) with `--history` and `--format json`, and add `aw meta repair` and `aw check meta`.
  Do not create a second `show`.
- The opt-in hooks extend to reject staged `meta/*.jsonl` changes that are not a pure append of
  valid events.

## 5. Installer and migration

### 5.1 Versioned migration chain (new)

- Today there is no numbered chain, and commit `19313eed` deleted the migration test suites. Add
  `agent_workflows/migrations/` with ordered, numbered migrations and a `metadata_schema` stamp in
  `.aw/config/project.json`. `aw install` runs pending migrations after the bundle install (dry-run
  report unless `--apply`/`-y`), and `aw migrate metadata` runs this one directly. `aw migrate` does
  NOT exist today; the existing `aw migrate-layout` is a separate top-level verb. Decide in plan step
  3 whether `migrate-layout` becomes `aw migrate layout` beside `aw migrate metadata`, so the CLI does
  not ship two migration spellings (see the CLI naming review, research `ffi66q`).
- Reuse `layout_migration.MigrationManager` machinery (transaction journal, writer lock, rollback)
  rather than inventing new ones.

### 5.2 Migration 0001 `metadata-v2` (hard cutover, one commit)

1. Preflight: clean tree for `.aw/records/`, no live run holding the integration lock, no lane
   worktrees with unmerged plan changes (report them; refuse without `--force`).
2. Export and fold the gitignored `.aw/records/history.jsonl` sidecar FIRST (`2vev8j` 6.2); it is
   the only copy of 306 records at review (240 backlog, 50 specs, 8 plans, 5 research, 3 other),
   and it exists only on the machine running the migration. A repository migrated on a machine
   WITHOUT that sidecar loses those records; the preflight must report the sidecar's presence and
   record count, and refuse without `--force` when a sidecar is expected but absent.
3. Mint an id6 for each LIFECYCLE record that has none in any form. Measured at review: 64 records
   (walkthroughs 15, implemented specs 14, executed prompts 13, comms 7, and a few others), NOT the
   ~542 the authored text gave; review records are EXCLUDED (4.1a) and account for 339 of the 549
   records lacking a `- Id:` bullet. `aw rename ... --to-id6` handles ONLY legacy timestamp names
   (`YYYYMMDD-HHMM-NN-<slug>`), so records whose names are already in another shape need a minting
   path the plan must name, rather than an assumption that the existing verb covers them.
4. For each artifact: parse with the CURRENT (legacy) readers, emit `checkpoint` (seq 0) holding
   every field, emit `legacy` events for every raw history line (`2vev8j` 4.7, optionally enriched
   with `inferred-from-git` ordering from `git log -p`), move prose fields into body sections, write
   the new two-key front matter and banner, delete the bullet block and `## Workflow history`. For a
   review record, emit one `review` event per round into the SUBJECT's log instead (4.1a).
4a. TERMINAL ARTIFACTS ARE MIGRATED TOO, AS A NAMED ONE-TIME EXCEPTION. MAINTAINER DECISION,
   2026-09-25, during spec review (finding SR-002). The repository forbids re-committing an executed
   plan (AGENTS.md: "Do NOT add commits to a plan already in `.aw/records/plans/executed/`"), and the
   `ipd-executed-gate` pre-commit hook enforces its terminal-state half. C9 (one format, no dual
   readers) means terminal artifacts cannot be left in the old format, so this migration commit is
   the single, deliberate exception: it rewrites every artifact in `executed/`, `superseded/`,
   `not-executed/`, `implemented/`, and `done/` (1055 files at review) with no change to their
   meaning. The hook must accept the migration's own commit through a positive, journaled marker the
   migration writes (the same kind of evidence finalize leaves), NOT through `--no-verify`, and must
   keep refusing any other edit to a terminal artifact after cutover (AC-16). AGENTS.md's rule is
   amended to name this exception. Rejected alternative: freezing terminal artifacts unmigrated,
   because it breaks C9 and leaves two formats in the tree permanently.
5. Delete `plans/STATUS.md`; remove the INDEX ignore lines from the `.aw/.gitignore` template;
   delete the INDEX files on disk.
6. Verify: automated round-trip (every legacy field value and raw history line recoverable from the
   logs), `aw check meta` clean, then stamp `metadata_schema: 2`.
7. Commit via `aw commit --no-plan` with the migration's own path list.

The legacy readers live ONLY in `migrations/m0001_metadata_v2.py` after the cutover, frozen, and are
deleted once no supported version needs to migrate from 1.x (C9).

### 5.3 Everything else refuses unmigrated repos

Any command that reads metadata checks `metadata_schema`; below 2 it exits nonzero with
"run `aw migrate metadata`" (AC-11).

### 5.4 Managed block, templates, docs

- `engine.py` managed block (AGENTS.md text on attestations, Status fields, `- From-Backlog:`,
  `- Blocks-Release:` field syntax), 25 workflow files (heaviest: `plan-review.md`,
  `assess/templates/ipd.md`, `assess/templates/orchestrator-ipd.md`, `templates/plans-README.md`,
  `spec-review.md`, `plan-review-long/03-resolve-and-finalize.md`), 5 records READMEs,
  `docs/artifact-lifecycles.md`, `ipd_schema.py` section schema, and the ipd-spec reference docs are
  rewritten to describe verbs (`aw set ... --priority`) instead of field syntax.
- Research `research_contract` YAML front matter folds into the same two-key format.

## 6. Blast radius and cost

| Area | Size | Work |
|---|---|---|
| Package modules touching metadata | 35 | Route to `artifact_meta`; delete local parsers |
| History-parsing modules | ~13 | Replace with `history()` |
| Filename-metadata code | ~20 sites | Unchanged (C10), but the ~8 bypassing `artifact_naming` should route through it while touched |
| Git-evidence code | 6 paths | Rewrite to compare logs (4.4) |
| Tests | 51 of 80 files; ~740 legacy-string hits; 17 fixtures | Rewrite fixtures via a shared builder; restore migration tests |
| Docs/workflows | ~35 files plus ~38 specs mentioning the format | Rewrite live docs; historical specs left as history |
| Corpus | ~1990 records | One scripted migration commit |
| Deleted | 4 INDEX files, STATUS.md, `plans_index`/`research_index` drift checks, ~9 parsers | |

Benefits: one parser instead of ~9; no INDEX drift or conflicts; tool-owned attestations; explicit
ordering and clone-safe history (closes `2vev8j` E1-E4 and backlog `hg2oop`); smaller artifact reads;
indexed queries (subsumes `59t9x5`, `8cpbia`).

Costs: metadata other than status no longer visible in the `.md` (mitigated by `aw show`); a large
one-time refactor concentrated in `runner_shared.py` (30k LOC), `check_engine.py`, `status_set.py`,
`attention.py`; a one-shot risky corpus migration (mitigated by dry-run, round-trip verification,
journal, and a single revertible commit).

## 7. Suggested plan decomposition (for the IPD Set)

1. `artifact_meta` API + event schema + field registry + tests (no callers yet).
2. SQLite cache + `aw show` + `aw index rebuild` (reads through the API).
3. Migration chain framework + `m0001_metadata_v2` with dry-run and round-trip verifier, run on a
   copy of this repo.
4. Route writers (`status_set`, `releases` setters, `specs`, `backlog`, `ipd_authoring`,
   `artifact_rename`, `plans_refs`, `plan_readiness`, `set_records`, finalize/retirement).
5. Route readers (`selectors`, `check_engine`, `attention*`, `ipd_lint`, `runner_shared`, runners,
   `plans*`, `research*`, `work_cmd`, `artifact_audit`, `review_findings`, hooks).
6. Delete INDEX/STATUS machinery and legacy parsers; add the AC-1 enforcement test.
7. Docs, managed block, templates, quickstarts.
8. Execute the migration on this repo in one commit; measure AC-13.

Steps 1-3 are additive and safe; 4-6 land together on one branch before 8, because C9 forbids a
dual-format period on `main`.

## 8. Open questions

- OQ-1 `[Non-blocking]` Exact per-type field registry, especially for prompts (id in an HTML
  comment today) and research (YAML today). Reviews are settled by 4.1a. Decide in plan step 1.
- OQ-2 `[Non-blocking]` Which record types carry front matter at all (walkthroughs, comms, research
  reference packages). Decide in plan step 1.
- OQ-3 `[Non-blocking]` Whether `aw install` runs migrations automatically with confirmation, or only
  reports them and requires `aw migrate metadata`. Recommended: report plus explicit command.
- OQ-4 `[Non-blocking]` Whether `2vev8j` is superseded outright or amended in place. Recommended:
  amend (it remains the authority for ordering, UTC, legacy import, and backward edges), with a
  pointer to this spec. NOTE the two specs contradict each other on two points, which is exactly
  what an amendment must reconcile: `2vev8j` C8 requires an INCREMENTAL, interruptible migration
  and its AC-11 requires a partially migrated corpus to be valid, while this spec's C9 requires a
  hard cutover with no dual readers; and `2vev8j` C4/4.5 keep current state and one history line
  inline, which this spec's 4.1 replaces. The amendment must state that C9 SUPERSEDES `2vev8j` C8
  and AC-11, and C1/4.1 supersede C4/4.5, citing the maintainer rulings of 2026-09-25, so a reader
  of `2vev8j` alone is not misled.
- OQ-5 `[RESOLVED 2026-09-25 by the maintainer]` How review records map onto a per-id6 log. See
  4.1a.
- OQ-6 `[RESOLVED 2026-09-25 by the maintainer]` Whether the migration rewrites terminal-directory
  artifacts despite the no-edit rule. See 5.2 step 4a.

## Workflow history
- 2026-09-26 same-status (aw set): Maintainer 2026-09-25: implementing this spec blocks the 2.0.0 release

- 2026-09-25 note (aw specs): /spec-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; SR-001..SR-013 FIXED; SR-001 (reviews logged in subject's log, new 4.1a) and SR-002 (terminal artifacts migrated as a named exception, 5.2 step 4a) decided by the maintainer; no Readiness written
- 2026-09-25 reviewed (aw set): /spec-review: APPROVE WITH REVISIONS APPLIED; SR-001..SR-013 all FIXED (SR-001, SR-002 by maintainer decision)

- 2026-09-25 to-review (aw specs): Authored from maintainer design discussion 2026-09-25
- 2026-09-25 created (aw specs): Move all aw artifact metadata and history into tracked per-artifact JSONL event logs at .aw/records/meta/<id6>.jsonl; compact front matter (id, status); gitignored SQLite index replaces INDEX.* and STATUS.md; hard cutover via aw migrate metadata
