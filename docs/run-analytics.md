# Run analytics

What this feature does: it reads the driver run directories this repository already writes, turns them
into a normalized fact table, caches that table incrementally, and publishes a self-contained offline
report plus a machine-readable query surface. Everything it produces stays on your machine, inside one
reserved, gitignored directory, unless you personally choose to share a bundle.

This document is written for four audiences at once, and each section says which it is for: an
operator running the commands, an agent consuming the records, a reviewer judging the privacy
boundary, and a maintainer diagnosing a bad number.

## Quick start (operator)

```sh
aw runs analyze                  # analyze every run, update the cache, publish the report
aw runs analyze --path           # print the report path; writes nothing, opens nothing
aw runs analyze --open           # open the published report in your browser
aw runs query overview           # the same numbers as structured records
```

Analytics is ENABLED by default and needs no install step. Every module ships in the package, so there
is nothing optional to add: the setup wizard gates ENABLEMENT, not code presence. That distinction
matters because a wizard that appeared to install something would leave you wondering whether a
missing number meant missing code.

`aw runs analyze` is the only analytics command that writes anything during normal use. It never
prompts, never touches a source run directory, never commits, and never reaches the network.

## Where everything is stored, and that it is disposable

Every artifact lives under the resolved runs root, in a reserved namespace:

```text
.aw/records/runs/analytics/
  cache/        one entry per analyzed run, keyed by a pseudonymous root id
  index.html    the latest published report
  analysis.json the latest report's data, as JSON
  snapshots/    immutable labeled copies you asked for with --keep-snapshot
  exports/      bundles written by `aw runs export --apply`
```

THE WHOLE TREE IS GITIGNORED AND DISPOSABLE. `.aw/records/runs/` is excluded from version control, so
nothing here is ever committed, and nothing here is a permanent record. Delete it and the next
`aw runs analyze` rebuilds it from the run directories. Two consequences worth stating plainly: do not
cite a file under this tree as durable evidence in a plan or a review, and do not expect anything here
to survive a clean checkout.

To remove it deliberately, use the wizard's deletion planner rather than a manual `rm`, so the plan is
shown before anything is unlinked.

## The commands

| Command | Writes? | What it is for |
| --- | --- | --- |
| `aw runs analyze` | yes, inside `analytics/` | update the cache and publish the report |
| `aw runs analyze --path` | no | print the latest report's path |
| `aw runs analyze --list` | no | list published artifacts and the cache summary |
| `aw runs analyze --rebuild` | yes | discard cached entries and recompute |
| `aw runs analyze --keep-snapshot LABEL` | yes | also publish an immutable labeled snapshot |
| `aw runs analyze --since WHEN --until WHEN` | yes | publish a report covering only runs started in that window |
| `aw runs query <view>` | no | structured facts, findings and refusals |
| `aw runs export` | only with `--apply` | build an inspectable, tiered bundle |
| `aw runs submit` | writes a local receipt | would transmit a bundle; refuses today |

Flag precedence on `analyze` is deliberate: `--path` and `--list` are read-only and are honored FIRST,
so asking where the report is never triggers a sweep.

Exit codes are the same three everywhere in this feature: 0 the work completed, 1 a domain finding
(for example a sweep that completed but skipped a run it could not read), 2 cannot-run (a usage error,
a disallowed query, or a refused slice).

## Limiting the dates a report covers

`--since` and `--until` restrict a sweep to runs that STARTED inside a window. Each accepts a date
(`2026-10-01`), a timestamp (`2026-10-01T06:00:00Z`), or a relative span (`30d`, `2w`, `6m`), the
same grammar `aw runs --since` uses. `--since` is inclusive. A bare date given to `--until` includes
that whole day, so `--since 2026-10-01 --until 2026-10-31` is all of October; a full timestamp is used
exactly. A window that ends before it starts is refused (exit 2) and nothing is published.

A run's start comes from its `state.json` `created_at`, or from the timestamp in its directory name.
A run with neither cannot be placed in a window, so when a window is set it is left out and the count
of such runs is reported, rather than being kept or dropped silently.

With a window (or explicit run targets) BOTH documents in the bundle cover only the selected runs, and
the dashboard header states the window. Without one, the report covers every run, as before. The
dashboard also has its own date range and quick ranges (last 7, 30 or 90 days, latest month) in the
side panel, which narrow the view further without re-running anything; those quick ranges count back
from the newest day in the data, not from today.

## Tokens and cost in the dashboard

The dashboard's **Tokens and cost** tab shows each kind of token on its own:

- **In + out**: input plus output, the tokens the model actually processed fresh.
- **Input**: uncached prompt tokens.
- **Output**: generated tokens.
- **Cached**: tokens read from the prompt cache.
- **Cache writes**: tokens written to the cache.
- **Total**: all of the above.

For each you can choose any of count, total, average, median and p90, shown for the whole selection
and split by a dimension. The default split is **Agent**, meaning the host and model together (for
example `oc / claude-opus`); any other dimension, such as model, stage or week, works too. The unit
selector at the top switches every figure between per session, per plan attempt and per plan run.

Costs appear beside the counts. The total is the cost the host recorded. Hosts record one cost per
step, not one per token kind, so the per-kind costs are APPORTIONED: the recorded cost is split in
proportion to each kind's token count times the price in effect that day, and the parts always add up
to the recorded total. Sessions with no recorded cost (all Antigravity sessions today) get no split
rather than an invented one. Cache writes and reasoning tokens have no known price, so they are counted
but never priced. Each session row also carries these values in the CSV download.

## Thinking, model time and model names

**Thinking tokens** are counted separately as `reasoning` (labelled "Thinking" in the dashboard),
and they are part of "in + out" and of the total. Two host details matter:

- OpenCode reports thinking beside output, and bills it at the output rate. This was measured by
  reproducing every priced step's recorded cost exactly.
- Antigravity reports thinking INSIDE `output_tokens`. The dashboard shows Antigravity output as the
  visible part only (output minus thinking), so thinking is never counted twice.

**Per-kind costs** are split step by step. For each step, the dashboard finds the published rate set
that reproduces that step's recorded cost exactly, and splits the cost into input, output, thinking
and cached parts that add up to the recorded total. Three rate sets cover every priced OpenCode step
in this corpus (USD per million tokens, input / output / cached):

| Rate set | Rates | Applies to |
| --- | --- | --- |
| era-a | 5.00 / 25.00 / 0.00 | everything before 2026-08-29 |
| era-b | 5.50 / 27.50 / 0.55 | Claude Opus 5 and unrecorded models |
| opus-5.5 | 4.40 / 22.00 / 0.22 | Claude Opus 5.5 |

A session whose steps match none of them (for example Gemini through OpenCode) shows its recorded
total with no split. Antigravity records no cost, so its sessions have tokens only.

**Time.** Hosts do not log thinking time. The dashboard reports **model time** (wall time minus time
spent inside tools) and an **estimated thinking time**: model time multiplied by thinking's share of
the tokens the model generated. Treat the second as an estimate, not a measurement.

**Model names** are shown in a readable form, for example
`uri/its_direct/pt3-claude-opus-5.5-1m-us` run at variant `high` reads as "Claude Opus 5.5 High".
Routing prefixes, deployment tags, the context-window marker, region and date stamps are dropped, and
the variant is added only when the run recorded one. The exact id stays in the data: it appears in
the session detail, the CSV download and `attempts.jsonl` as `model_id` and `model_variant`. To
correct a name, add an override to `.aw/config/project.json`; the variant is still appended:

```json
"model_display_names": {
  "uri/its_direct/pt3-claude-opus-5.5-1m-us": "Claude Opus 5.5"
}
```

## Review cost: per-attempt analysis

Every `aw runs analyze` also publishes `attempts.jsonl` beside the dashboard: one row per agent
session, built from the session logs. Three `aw runs query` views read it, and the dashboard's
**Review cost** tab shows the same figures. Run `aw runs analyze` first; until it has run, these
views say so and exit 2.

By default the views count only each queue attempt's MAIN session. Add `--filter phase=verifier`,
`--filter phase=recovery` or `--filter role=<role>` to see the others.

| Question | Command |
| --- | --- |
| How a phase's tokens split, with token and cost shares | `aw runs query attempts --filter role=main --group-by phase --stat sum` |
| Composition, steps and context for reviews | `aw runs query attempts --filter action=review --metric input,cache_read,cache_write,output,reasoning,steps,context_first,context_last,context_max` |
| Cost against step count | `aw runs query attempts --filter action=review --group-by step_bucket --metric cost,steps` |
| New versus reused host session | `aw runs query attempts --filter action=review --group-by session_origin --metric context_first,cost,steps` |
| Tool calls, output bytes, shell commands, files read | `aw runs query tools --filter action=review` |
| By toolkit commit or run label | `aw runs query attempts --group-by code_commit` (or `label`, `review_variant`, `repo_commit`) |
| Model, and where the model id came from | `aw runs query attempts --group-by phase,model_source --metric steps --stat count` |
| Redo counts per model | `aw runs query attempts --group-by model --metric redo_total,turn_retries,refusals,reasks --stat sum` |
| Experiment comparison: review outcome (disposition and Readiness) per plan, variant and model | `aw runs query experiment --filter label=<label>` |
| Attempts by Readiness | `aw runs query attempts --filter action=review --group-by readiness --metric cost,steps` |
| Attempts by review tier | `aw runs query attempts --filter action=review --group-by review_tier --metric cost,steps` |
| Attempts by review step | `aw runs query attempts --filter action=review --group-by review_step --metric cost,steps` |

What the fields mean:

- **Context** at a step is new input plus cache reads plus cache writes for that step.
  `context_first`, `context_last` and `context_max` are taken over an attempt's model steps.
- **step_bucket** groups attempts by model steps in buckets of 25 (`000-024`, `025-049`, ... `200+`).
- **session_origin** is `new` when the attempt's host session was first used in the run, `reused`
  when an earlier queue item already used it, `continued` when only the same item used it before
  (a retry), and `unknown` when the log carried no session id.
- **phase** is `review`, `execute` or `plan` for a main turn, `verifier` for any verifier session,
  and `recovery` for recovery attempts and corrective sessions (gate answers, defect re-asks,
  merge-conflict and red-CI repairs, review-orchestrator corrections).
- **Redos** count turn retries, refusals (begin, finalize, clean base, reintegration, red CI) and
  re-asks (defect re-asks and review-orchestrator corrections), each attached to the attempt it
  interrupted.
- **Command families** are the program of each shell command, plus its subcommand for multi-verb
  tools (`git log`, `aw ipd lint`). Heredoc bodies and quoted text are ignored, and no arguments
  are kept.
- **Files read** are counted per path, made relative to the repository so the same file reads the
  same in every worktree. A path outside the repository keeps only its last two parts.
- **Experiment** gives one row per plan, review variant and model. Each row covers every attempt
  of that plan, and the verifier sessions that checked them. Where no cost was recorded it reports
  tokens. The outcome is the final disposition (`reviewed`, `approved`, `fail-gate`). The `readiness`
  count map tallies the normalized `- Readiness:` value (`go`, `go-pending-approval`, `no-go`) recorded
  on review attempts from this plan's commit onward; `absent` means the review wrote no valid value,
  and `(not recorded)` means the run predates the recording.

A group smaller than the shared minimum sample (12) keeps its counts and totals, but its medians and
percentiles are withheld and the row says so.

### What is not recorded yet

- **Antigravity cost**: tokens are reported; no dollar price table is applied.
- **Readiness on older runs**: runs started before this change do not carry `review_readiness` on their review attempts, so they report `(not recorded)`.

### Labeling runs for an experiment

`aw oc run` and `aw agy run` accept `--label TEXT` and `--review-variant NAME` on `start`. Both are
recorded in `state.json` under `options` and change nothing about how the run behaves. Every run
started from this version also records a `git` block: the repository's full HEAD commit at run start,
whether the working tree was dirty, and the toolkit version. Older runs have none of these. For an
older run, the toolkit commit is read from its telemetry where available, and the repository commit
from its first attempt.

## The agent surface

`aw runs query` exists so an agent never has to parse the report HTML. Add `--agent` for
`aw.agent/v1` JSONL, or `--json` for the full structured representation; `--agent` must be passed
explicitly, and piping affects color only.

The views are `overview`, `schema`, `metrics`, `distributions`, `slices`, `findings`, `evidence`,
`data-quality`, `cache-status` and `explain`. Run `aw runs query schema` to print the live list along
with every allowlisted filter field, grouping field, metric and statistic.

Queries are ALLOWLISTED, not expressive: there is no SQL, no expression evaluation, no unrestricted
field projection, and no filesystem path outside the resolved analytics roots. Results are bounded by
default and report `total`, `emitted` and `omitted` plus the exact command that continues the page,
because a silently truncated answer is indistinguishable from a complete one.

## Reading a number honestly

Every value carries its PROVENANCE, and the four states are not interchangeable:

- `recorded`: a number the driver or provider actually wrote down.
- `measured`: a number computed from two recorded observations, such as a duration from a start and an
  end timestamp.
- `derived`: a number computed through a model, such as a cost estimated from a price table.
- `missing`, `unavailable`, `not-applicable`: three different kinds of absence, and NONE of them is
  zero.

That last line is the one that prevents the most common misreading. A verify phase that never ran is
`not-applicable`; a phase whose driver generation could not record usage is `unavailable`; a phase that
should have a number and does not is `missing`. Summing them as zero would report a free run.

Token components CONSERVE: the named components add up to the recorded total, and a violation is
flagged rather than silently corrected. Time accounting reports wall time, observed activity, overlap
and unattributed time separately, so overlapping intervals are never double counted.

## Analyses that REFUSE, and why a refusal is the right answer

Some analyses come back `cannot-determine` with an observed sample size, and `aw runs query` returns
that refusal (exit 2, with the observed n) rather than a number. This is deliberate. An empty chart reads
as "we measured zero", which is a stronger and falser claim than silence; omitting the analysis is
indistinguishable from an oversight; and plotting the three points that do exist is a fabrication.

So when you see a refusal, read it as "this corpus does not contain enough of this thing to say
anything", check the reported n, and gather more runs if you need the answer. A refusal is not a bug,
and a tool that turned one into a number would be worse than one that refuses.

## Cost, prices and the two eras

Costs the provider RECORDED are used as recorded. Costs the tool computed from a price table are
`derived` and labeled as estimates, and the price table is EFFECTIVE-DATED, so a run is priced with
the prices in force when it ran rather than with today's. Where a model has no price entry, no cost is
invented; the value is absent with a reason.

## Model attribution and per-attempt resolution

Model identity is resolved per attempt rather than once per run. This ensures that verifier turns and executor turns with different model configurations are accurately reported across dashboard rows and analytics facts.

Resolution follows a strict fallback precedence:

1. Observed host model from the execution host (when present).
2. Frozen launch model requested for the turn.
3. For verifier roles, the attempt's verifier twin fields before executor fields.
4. Run-level options model or explicit model.
5. Run-level cost attribution model (or verify cost attribution).
6. Unrecorded, labeled per host when absent.

Historical runs recorded before per-attempt model capture are not back-filled. For those runs, model attribution falls back cleanly to the run-level options tiers so no existing run loses attribution.

## Telemetry

| Setting | Default | Why |
| --- | --- | --- |
| basic start/end telemetry | ON | two events per execution, no measurable cost, and it is what makes a duration interpretable at all |
| periodic resource sampling | OFF | unbounded in count, so it is a separate, explicit opt-in |
| sample interval | 15 s, clamped to 1 s .. 3600 s | the floor exists because every event is fsynced, so a sub-second interval would compete with the run it measures |

Telemetry is configured under the `run_analytics_telemetry` key in `.aw/config/project.json` (portable,
committed) or `.aw/config/local.json` (machine-local, never committed). A malformed or out-of-range
value lands on the documented default rather than failing the run.

TELEMETRY IS PSEUDONYMOUS, NEVER ANONYMOUS. Node identity is recorded as a salted pseudonym, and a
pseudonym is stable enough to correlate records, which is exactly what makes it useful and exactly why
it is not anonymity. Measured per-sample cost on one Linux machine at 12 cores, for scale rather than
as a guarantee: about 161 microseconds per full system probe, about 4 microseconds for the framing
alone.

A probe that cannot answer records WHY (permission denied, timed out, malformed output) instead of
reporting a zero.

## The cache, and when it rebuilds

The cache holds one entry per run, and a sweep decides HIT or REBUILD per run with a reason code you
can read in `aw runs query cache-status`:

| Situation | Decision | Reason |
| --- | --- | --- |
| unchanged, finished run with a valid entry | hit | `fresh-complete-entry` |
| first time seen, or newly added | rebuild | `no-entry` |
| an analytics-relevant input or the producer vocabulary changed | rebuild | `fingerprint-changed` |
| the run is still live, or was resumed | rebuild | `run-not-terminal` |
| the entry was stored mid-run | rebuild | `entry-incomplete` |
| the entry came from another cache schema | rebuild | `schema-version-mismatch` |
| the entry is corrupt or unreadable | rebuild | `entry-unreadable` |
| another analyzer holds that entry | skip | `lock-busy` |

Two behaviors worth knowing. A RESUMED run reuses its directory, so the terminal state is checked
BEFORE the file fingerprint: "the files did not change" is not evidence of stability for a run that
may still be writing. And a contended entry SKIPS with a reason rather than waiting, because the work
is recomputable, so a skip costs one rebuild next time while a block would cost you your command.

A release that adds or removes an analytics metric automatically rebuilds affected entries on the
next ordinary `aw runs analyze`, because the producer's declared vocabulary participates in the
fingerprint. Upgrades self-heal without operator intervention, so you do not need to run a manual
rebuild when a new metric lands.

Recovery from damage needs no special verb: one corrupt run degrades ITSELF, the sweep completes over
the rest, and the skipped run is reported. `aw runs analyze --rebuild` remains available for a damaged
or hand-edited tree; it discards cached entries and recomputes without touching a source run.

Removals are found by comparing your run list against the cache listing, not by a decision: a run that
is gone is not enumerated, so it produces no verdict at all.

## The report bundle, and what "offline" was actually tested to mean

The published `index.html` is self-contained: no external stylesheet, no CDN script, no font fetch, no
dynamic import. What was TESTED is that the bundle is read from a `file://` path (including paths
containing spaces and non-ASCII characters) with sockets denied, issuing zero connection attempts, and
that a static scan of the document finds zero network references. What was NOT tested is behavior in
any particular browser engine, so treat "works offline" as a property of the bundle rather than a
promise about your browser.

Large corpora stay usable: the data is embedded once as columns, the dashboard draws charts from
grouped values rather than one element per row, and the session table pages 100 rows at a time.

## Sharing data: export tiers and what each one really contains

`aw runs export` PREVIEWS by default. Without `--apply` it reports exactly what would be written and
writes nothing.

| Tier | Contents | Requirement |
| --- | --- | --- |
| `metrics` (default) | facts that already crossed the write-side privacy projector | none |
| `events-redacted` | adds bounded structured event facts, field-allowlisted | none |
| `raw` | ORIGINAL run artifacts: prompts, conversations, code, commands, paths, possibly secrets | `--by-human` attestation AND an explicit `--include` selection |

NO TIER IS ANONYMOUS, and no tier claims to be. `metrics` is minimized and pseudonymized,
`events-redacted` is field-allowlisted, and `raw` is original content. Minimization is not anonymity.
Each bundle carries its own README and manifest saying so, so the caveat travels with the data instead
of living only here.

Bundles are never transmitted as a side effect of building one. `aw runs submit` exists, refuses today
because no endpoint is approved, and would require an explicit human attestation if one were. It
writes a local receipt recording the destination by scheme and host only and the credential by
environment variable NAME, never a value, because a receipt outlives the command and gets pasted into
bug reports.

## The privacy boundary: what is guaranteed, what is detected, and what is neither

THIS IS THE MOST IMPORTANT SECTION IN THIS DOCUMENT, so it states its limits before its assurances.

**The guarantee is STRUCTURAL.** Facts reach the cache through a write-side ALLOWLIST that REFUSES an
unnamed key rather than dropping it, so sensitive content cannot arrive under a field nobody
anticipated; the whole write fails instead. The export tiers narrow further by CONSTRUCTION: the
redacted events payload is built by iterating the allowlist and copying only named fields, so there is
no code path by which an unnamed key is written. That holds for content no pattern would have matched,
which is why it, and not detection, is the guarantee.

**The detector is CORROBORATION, and its blind spots are named here on purpose.** The repository's
shared leak detector is run over produced artifacts as a second opinion. Measured against the thirteen
sensitive-content classes the export layer enumerates, it catches TWO at fail severity:

- `filesystem-path`
- `username`

and does NOT look for the other ELEVEN:

- `prompt-text`
- `response-text`
- `shell-command`
- `hostname` (advisory only, not fail severity)
- `git-remote`
- `branch-name`
- `commit-message`
- `environment-secret`
- `high-entropy-token`
- `spreadsheet-formula`
- `archive-traversal`

It has no entropy test and no secret-shape rule. Three of its fail rules are compiled from this
repository maintainer's own tokens, so on any other machine its measured coverage is LOWER than the
figure above.

**Therefore: never read "the sanitizer found nothing" as a privacy guarantee.** For eleven of thirteen
classes a clean detector result and an unexamined file are the same result. The assurance is the
allowlist; the detector can raise confidence and cannot establish safety. The export layer ships this
same enumeration inside its own report rather than only in documentation, so a bundle carries its
limits with it.

**One more limit, for reviewers.** The repository's `aw sanitize` walk enumerates TRACKED files, and
the analytics tree is gitignored, so pointing that command at this feature's output reports clean
BECAUSE IT CANNOT SEE IT. That is not a defect in the sanitizer; it is the wrong tool for a gitignored
tree. The feature's own tests therefore scan artifact CONTENT through the same detection engine, and
pair every scan with a control proving the scan can fail.

## What this feature does not tell you

- It shows CORRELATION, never causation. A Set that ran faster after a change may have run faster for
  ten other reasons.
- It does not anonymize, and it says so everywhere rather than once.
- It changes no workflow and selects no model. It reports; you decide.
- It refuses under-powered analyses instead of estimating them, so some questions will have no answer
  until the corpus grows.

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| `aw runs analyze --path` exits 2 | no report published yet; run `aw runs analyze` first |
| a run is reported skipped | that run's inputs were unreadable or its entry was contended; rerun, and if it persists inspect that run directory |
| every run rebuilds each time | the runs are not terminal (still live or resumable), which is correct behavior, not a cache failure |
| a query refuses with `cannot-determine`, or a dashboard median shows `-` | the group is under-powered; check the reported n |
| a cost is absent | the provider recorded none and no price entry covers that model; absence is deliberate, not an error |
| the dashboard opens but is unstyled | the packaged browser assets are missing from your install; reinstall the package |
| numbers changed with no code change | the corpus changed; the cache is derived from the run directories and they are mutable |

## Compatibility

Every driver generation this repository has written is readable: the current runner, and both legacy
generations. The generation is inferred from the driver path recorded in each run rather than from a
schema version, because the version has been uniform across generations and cannot discriminate them.
An unrecognized future driver is recorded as `unknown` and ingested on a best-effort basis rather than
refused.

Agy-host support is written against the Agy runner's code and synthetic fixtures. No Agy run has been
observed on disk in this repository, so Agy conformance is NOT corpus-validated, and this document will
not claim otherwise.
