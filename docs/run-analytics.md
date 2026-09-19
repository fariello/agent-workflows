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
| `aw runs query <view>` | no | structured facts, findings and refusals |
| `aw runs export` | only with `--apply` | build an inspectable, tiered bundle |
| `aw runs submit` | writes a local receipt | would transmit a bundle; refuses today |

Flag precedence on `analyze` is deliberate: `--path` and `--list` are read-only and are honored FIRST,
so asking where the report is never triggers a sweep.

Exit codes are the same three everywhere in this feature: 0 the work completed, 1 a domain finding
(for example a sweep that completed but skipped a run it could not read), 2 cannot-run (a usage error,
a disallowed query, or a refused slice).

## The agent surface

`aw runs query` exists so an agent never has to parse the report HTML. Add `--agent` for
`aw.agent/v1` JSONL, or `--json` for the full structured representation; `--agent` is automatic when
the output is piped.

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

Some analyses come back `cannot-determine` with an observed sample size, and the report renders those
as a first-class refusal panel rather than as an empty chart. This is deliberate. An empty chart reads
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
| an analytics-relevant input changed | rebuild | `fingerprint-changed` |
| the run is still live, or was resumed | rebuild | `run-not-terminal` |
| the entry was stored mid-run | rebuild | `entry-incomplete` |
| the entry came from another cache schema | rebuild | `schema-version-mismatch` |
| the entry is corrupt or unreadable | rebuild | `entry-unreadable` |
| another analyzer holds that entry | skip | `lock-busy` |

Two behaviors worth knowing. A RESUMED run reuses its directory, so the terminal state is checked
BEFORE the file fingerprint: "the files did not change" is not evidence of stability for a run that
may still be writing. And a contended entry SKIPS with a reason rather than waiting, because the work
is recomputable, so a skip costs one rebuild next time while a block would cost you your command.

Recovery from damage needs no special verb: one corrupt run degrades ITSELF, the sweep completes over
the rest, and the skipped run is reported. `aw runs analyze --rebuild` discards cached entries and
recomputes; it never touches a source run.

Removals are found by comparing your run list against the cache listing, not by a decision: a run that
is gone is not enumerated, so it produces no verdict at all.

## The report bundle, and what "offline" was actually tested to mean

The published `index.html` is self-contained: no external stylesheet, no CDN script, no font fetch, no
dynamic import. What was TESTED is that the bundle is read from a `file://` path (including paths
containing spaces and non-ASCII characters) with sockets denied, issuing zero connection attempts, and
that a static scan of the document finds zero network references. What was NOT tested is behavior in
any particular browser engine, so treat "works offline" as a property of the bundle rather than a
promise about your browser.

Large corpora degrade gracefully rather than hanging: the payload is stored columnar and compressed,
plotted series are pre-binned so DOM node count does not grow with row count, and the raw data view
paginates.

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
| a chart is a refusal panel instead of a chart | the analysis was under-powered; check the reported n |
| a cost is absent | the provider recorded none and no price entry covers that model; absence is deliberate, not an error |
| the report opens but is unstyled | the packaged browser assets are missing from your install; reinstall the package |
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
