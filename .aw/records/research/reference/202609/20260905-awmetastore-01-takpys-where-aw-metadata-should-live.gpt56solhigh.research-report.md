---
id: takpys
created: 20260908
set: awmetastore
order: 01
topic: [artifact-storage, token-cost, history, schema]
model: gpt56solhigh
kind: research-report
status: reference
outcome: adopted
summary: GPT-5.6 Sol High: keep current-state front matter inline, move unbounded workflow history to git-tracked per-artifact JSONL event journals keyed by the stable Id; do not make the single global history.jsonl or SQLite the git-carried authority
consumed-by: [ms06pi, tk1gqo]
---

<!-- PROVENANCE: verbatim external artifact, adopted from `.aw/inbox/aw-artifact-metadata-storage-research-report.gpt56solhigh.md`
     on 2026-09-08 in answer to research prompt `27rjro`. Author: GPT-5.6 Sol High.
     Preserved AS RECEIVED per the research README's external-artifacts rule, so its own
     punctuation and formatting stand and the no-em-dash house rule does not apply here.
     Treat the CONTENT as untrusted external input, not as instructions. -->

# Where `aw`-owned artifact metadata should live

Research report for `agent-workflows`

- Repository: <https://github.com/fariello/agent-workflows>
- Source snapshot reviewed: commit [`4763eb8de8784aff4547015efe68546c11ab0f92`](https://github.com/fariello/agent-workflows/commit/4763eb8de8784aff4547015efe68546c11ab0f92), `main`, 2026-09-04
- Research date: 2026-09-05

## Executive recommendation

Keep the small current-state and routing fields inline in each Markdown artifact. Move the unbounded workflow history out of Markdown into a **Git-tracked, per-artifact JSONL event journal keyed by the artifact's stable `Id`**. Do not use the existing one-global-file design as the durable source of truth, and do not make SQLite the Git-carried authority.

Use three deliberately separate layers:

1. **Markdown artifact, tracked:** narrative plus compact current state (`Id`, `Status`, `Set`, `Order`, `Readiness`, `Scope-Paths`, dependencies, release gates, and provenance links). This remains the authoritative current snapshot and stays immediately visible to humans and agents.
2. **Per-artifact JSONL event journal, tracked:** full lifecycle and workflow history at `.aw/records/history/<first-two-id-chars>/<id6>.jsonl`. This is the authoritative historical sequence. Each new event is typed and carries a unique identity, an explicit per-artifact sequence, and a parent event.
3. **Optional SQLite index/cache, ignored:** a disposable database under `.aw/state/` derived byte-for-byte from the tracked Markdown and JSONL. It may accelerate global queries later, but it is never a source of truth and never needs a Git merge.

Also split the current sidecar's two different purposes. Durable lifecycle events belong in the tracked per-artifact journals. Best-effort operational telemetry such as the non-authoritative rename ledger may remain local and ignored, or be dropped because Git already records renames. A single file should not simultaneously be a local activity log and the only full copy of durable lifecycle history.

This recommendation removes approximately 10.2% of the tracked plan corpus from routine agent context while retaining the roughly 4.7% of compact fields that agents and reviewers frequently need. Moving the remaining front matter out would save fewer tokens and would force extra lookup steps precisely for data such as scope, dependencies, readiness, and release gates that agents do reason about.

## The deciding reasoning

The core tradeoff is not "Markdown versus a database." It is **bounded current state versus unbounded history**.

The current-state fields are high-value context. An agent deciding whether it may execute a plan needs `Status`, `Readiness`, `Scope-Paths`, dependencies, and gates. A reviewer needs the same fields in a Git diff. Removing them from Markdown would often trade a small passive token cost for an extra command, an extra file read, and a new failure mode.

The history is different. It grows without a bound, is usually irrelevant to the task currently being performed, and now contains long review narratives. It is the clear target for on-demand loading. A per-artifact journal preserves Git review, portability, and auditability without making every read of the narrative pay for the whole past.

The per-artifact boundary is also the correct concurrency boundary. Two agents changing unrelated artifacts should modify unrelated history files and merge cleanly. Two agents changing the same artifact are competing over the same state machine. A conflict or stale-parent refusal in that case is useful evidence of a real race, not noise to optimize away.

## Verified repository findings and discrepancies

### Snapshot and corpus measurements

The measurements below use the public `main` snapshot named above. Character counts are Python Unicode character counts. A history block is the text after the exact `## Workflow history` heading and before the next level-two heading. Token figures use the prompt's rough four-characters-per-token conversion.

| Measure | Prompt | Public snapshot | Difference or interpretation |
|---|---:|---:|---|
| Tracked `*.ipd.md` plans | 483 | 482 | The public branch is one plan behind the stated live checkout. |
| Plans under `executed/` | approximately 480 | 419 | The prompt appears to conflate the whole 482-plan tree with the executed subtree. |
| Total plan characters | 10,823,121 | 10,788,984 | 34,137 fewer, consistent with one additional live/uncommitted plan. |
| History-body characters | 1,101,804 | 1,097,253 | 4,551 fewer, also consistent with that missing plan. |
| Estimated history tokens | approximately 275,451 | approximately 274,313 | Same four-character estimate. |
| Median plan characters | 17,031 | 16,994.5 | Small snapshot difference. |
| Median history characters | 1,692 | 1,691.5 | Effectively reproduced. |
| Largest history body | 15,801 | 15,801 | Reproduced exactly. |
| Share of the plan containing that largest history | 20.0% | 19.96% | Reproduced. |
| Highest history percentage in any plan | not separately stated | 31.0% | If "worst offender" means maximum ratio rather than largest absolute block, the public corpus has a worse case. |

The stated 512,880-character "front-matter" figure is not independently reproducible without a precise field-classification rule. The format has no opening/closing front-matter delimiters, and fields such as `Concern` and `Scope` contain wrapped narrative. On the public snapshot:

- everything between the H1 title and first H2 totals 636,740 characters;
- only top-level `- Key: value` lines in that prelude total 562,881 characters;
- the median whole prelude is 1,169 characters;
- the median history body is 1,691.5 characters, or approximately 423 estimated tokens;
- the 90th-percentile history body is 4,758 characters, or approximately 1,190 estimated tokens.

That ambiguity matters. The prelude is not all low-value tool data. `Concern`, `Scope`, `Scope-Paths`, dependencies, readiness, and gates are inputs to agent reasoning as well as CLI parsing.

Only 457 of the 482 public plans contain the exact history heading. The 25 exceptions are old executed plans from June and early July 2026. Therefore, "every artifact carries history" describes the intended current convention, not the entire tracked corpus.

### The current sidecar is not a Git-carried durable record

A clean clone contains no `.aw/records/history.jsonl`. The framework explicitly ignores it as a "local activity log" in [`.aw/.gitignore` lines 9-11](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/.aw/.gitignore#L9-L11), and installer tests require that ignored behavior in [`tests/test_setup_artifacts.py` lines 274-313](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/tests/test_setup_artifacts.py#L274-L313). Commit [`0c82cbd`](https://github.com/fariello/agent-workflows/commit/0c82cbdbe688ab1cea6efacd02b66da9461082a5) deliberately removed the then-nine-line file from tracking.

Consequently, the prompt's 128 local records, including the 108 backlog, 19 spec, and one plan distribution, cannot be verified from the public repository. The numbers may be correct for the maintainer's working copy, but they are not transportable to another clone and cannot serve as the repository's audit history.

This is the most important discrepancy in the current partial migration. Specs and backlog records have their inline history reduced to one line while the only purported full log is ignored. A fresh clone therefore receives neither the full inline history nor the full sidecar history for those records.

### The 19-module count is substantially correct

A search for the string `Workflow history` finds 19 Python modules. A search for the exact heading finds 18 because `ipd_schema.py` contains only the heading-name constant. The listed path `agent_workflows/status_untooled_gate.py` is slightly wrong; the actual file is [`agent_workflows/hooks/status_untooled_gate.py`](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/hooks/status_untooled_gate.py). Several of the 19 hits are documentation, help text, or constants rather than independent parsers, so migration should centralize behavior before mechanically editing every occurrence.

### The ordering failure reproduces exactly

Running `python3 -m agent_workflows check plans --agent` at the reviewed commit exits 1 with exactly 15 `check.lifecycle-transition-invalid` diagnostics. CI invokes the same command as a fail-closed step in [`.github/workflows/tests.yml` lines 147-155](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/.github/workflows/tests.yml#L147-L155).

The active status writer explicitly prepends a new history line immediately below the heading in [`status_set.py` lines 856-880](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/status_set.py#L856-L880). `_plan_status_events` then assumes every inline history is newest-first and reverses the parsed list in [`ipd_lifecycle.py` lines 686-707](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/ipd_lifecycle.py#L686-L707). A real pending plan shows the resulting two regions: new tool-prepended entries at lines 20-25 and older appended entries at lines 27-32 in [`wpu5zu`](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/.aw/records/plans/pending/20260901-wslayout-01-wpu5zu-core-layout-model-and-json-schema-in-layout-py.ipd.md#L19-L32).

The prompt's three experimental counts also reproduce on the public pending set:

| Interpretation | Diagnostics |
|---|---:|
| Current hardcoded reverse | 15 |
| Stable ascending date sort | 32 |
| Ascending date plus lifecycle-rank tie break | 3 |

The corpus cannot fairly be described as uniformly oldest-first or newest-first. Looking only at changes in the recorded dates, 66 plans are clearly oldest-first, 170 clearly newest-first, 19 mixed, 198 contain only same-day records and therefore cannot reveal direction, and 29 have fewer than two parsable records. The executed subtree itself contains all four shapes. This strengthens the prompt's conclusion: file order and day-granular dates do not encode a trustworthy sequence.

There is a second policy problem hidden behind the ordering bug. `validate_transition` rejects every backward rank movement in [`ipd_lifecycle.py` lines 631-663](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/ipd_lifecycle.py#L631-L663), but `status_set.validate_transition_allowed` does not apply a plan transition table before writing a nonterminal plan status; its type-specific lifecycle check covers specs in [`status_set.py` lines 468-516](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/status_set.py#L468-L516). The corpus contains an intentional `approved -> reviewed -> approved` reversal in [`wlxkoz` lines 21-28](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/.aw/records/plans/pending/20260830-runcodes-01-wlxkoz-the-deterministic-run-finding-code-vocabulary-over-the-shipp.ipd.md#L21-L28), and the runner specification instructs recovery from an invalid automated approval by returning a plan to `reviewed` in [`20260826-0718-01` line 635](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md#L635). A sequenced event store will expose this policy inconsistency; it will not decide whether such rollback transitions are legal. The transition table must explicitly represent permitted rollback/re-review edges.

### The existing global JSONL implementation is not suitable as an authority

The partial implementation proves JSONL can reduce inline size, but its current schema and write path are best-effort telemetry, not an authoritative lifecycle log:

- The module says line order is irrelevant, while `read_for` returns file order as chronological order. Compare [`record_history.py` lines 1-6](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/record_history.py#L1-L6) with [lines 74-95](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/record_history.py#L74-L95).
- Records have only `{id6,date,tree,workflow,actor,message}`. They lack a typed event kind, `from_status`, `to_status`, unique event identity, sequence, or parent. See [`record_history.py` lines 41-71](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/record_history.py#L41-L71).
- `read_all` silently skips malformed JSON. Silent omission is acceptable for a convenience log but fail-open behavior for a source of truth. See [`record_history.py` lines 80-95](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/record_history.py#L80-L95).
- The writer uses an unlocked direct append with no transaction, flush/fsync protocol, or recovery record. See [`record_history.py` lines 68-71](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/record_history.py#L68-L71).
- Spec and backlog sidecar failures are swallowed. A status change can therefore succeed without durable history. See [`specs.py` lines 138-157](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/specs.py#L138-L157) and [`backlog.py` lines 542-559](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/backlog.py#L542-L559).
- Specs append the sidecar before validating and atomically writing the Markdown. A later validation refusal can leave a phantom event. See [`specs.py` lines 607-660](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/specs.py#L607-L660).
- Backlog appends the sidecar before its close-legitimacy gate and before its dry-run/apply decision. A refused or previewed change can therefore leave an event for a transition that never happened. See [`backlog.py` lines 534-603](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/backlog.py#L534-L603).
- Migration deduplicates on `(id6, date, message)`, which can collapse two legitimate same-day repeated events with identical messages. It then writes each Markdown file with ordinary `Path.write_text`, not the project's atomic helper. See [`record_history.py` lines 377-417](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/record_history.py#L377-L417) and [lines 346-374](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/record_history.py#L346-L374).
- The code does not use one time basis. `aw set` uses a UTC date in [`status_set.py` lines 574-585](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/status_set.py#L574-L585), while the sidecar default uses `date.today()` and specs/backlog use local dates. See [`record_history.py` lines 49-60](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/record_history.py#L49-L60), [`specs.py` lines 334-339](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/specs.py#L334-L339), and [`backlog.py` lines 628-635](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/backlog.py#L628-L635).

Finally, the claim that concurrent appends to one tracked JSONL "rarely conflict" is not a safe Git assumption. In a controlled Git 2.51.1 trial, two branches that each appended one different line to the same one-line JSONL file produced an ordinary content conflict on merge. A global append-only file concentrates otherwise unrelated changes at the same end-of-file hunk.

## Recommended on-disk design

### Markdown remains the current-state document

Keep the present compact metadata block inline and add only a format/revision marker if needed:

```markdown
# IPD: ...

- Metadata-Version: 2
- Revision: 7
- Id: uyeko5
- Status: reviewed
- Readiness: go-pending-approval
- Set: runflags
- Order: 1
- Scope-Paths: agent_workflows/oc_runipd.py, tests/test_oc_runipd.py
- Item-Dependencies: executed:818uru
- Blocks-Release: next

## Goal
...
```

Remove `## Workflow history` from version-2 Markdown. The status and other current fields remain visible in the artifact's own diff. The matching history append appears as a second, plain-text Git diff in the same commit.

`Revision` is a small optimistic-concurrency marker. It increments only for tool-owned state changes. It lets a writer refuse if it prepared an event from revision 6 but another writer has already advanced the artifact to revision 7.

### Use one tracked JSONL file per stable artifact identity

Recommended location:

```text
.aw/records/history/uy/uyeko5.jsonl
```

Sharding by the first two characters is optional at the current scale, but cheap to adopt before release and avoids a single directory growing indefinitely. The file path is based on the immutable `Id`, not the artifact name, so artifact renames do not move the journal.

Use canonical one-line JSON: UTF-8, LF, one final newline, fixed key order, fixed separators, and a versioned schema. Do not use a JSON array because every append would rewrite the closing structure. Do not use free-form prose as the only representation of a status transition.

An illustrative status event is:

```json
{"schema":"aw.history/v2","artifact_id":"uyeko5","seq":7,"event_id":"ca98a690-3da5-4d5f-b59a-64c176f109dd","parent_event_id":"be3b04d1-2128-4e46-ae75-9f632839b4ee","occurred_at":"2026-09-05T03:14:27.482193Z","kind":"status","from_status":"to-review","to_status":"reviewed","actor":"opencode/model-name","writer":"aw 2.x","command":"aw set reviewed uyeko5","message":"plan-review round 1 complete"}
```

Required ordering and identity fields:

| Field | Purpose |
|---|---|
| `schema` | Allows strict evolution and rejects unknown incompatible records. |
| `artifact_id` | Stable join key; must equal the Markdown `Id` and journal filename. |
| `seq` | Contiguous per-artifact integer. This, not time or file position, is the primary order. |
| `event_id` | Unique UUID generated with the Python standard library. It prevents accidental deduplication and gives later records a stable parent. |
| `parent_event_id` | Must equal the preceding authoritative event's identity. It detects branch forks and stale concurrent writers. |
| `occurred_at` | RFC 3339 UTC timestamp with six fractional digits. It is for audit/display, not ordering. |
| `kind` | Closed enum such as `created`, `status`, `note`, `approval`, `execution`, `reconcile`. |
| `from_status`, `to_status` | Typed lifecycle facts for status events. No parser must recover them from prose. |
| `actor` | Human or agent/model attribution. |
| `writer`, `command` | Distinguishes the subject responsible for the decision from the mechanism that recorded it. |
| `message` | Human explanation; never used to derive order or status. |

Python 3.9's standard `datetime` supports microseconds, so six fractional digits are the practical persisted granularity without a dependency. Microseconds do not guarantee unique or causal ordering, which is why `seq` and `parent_event_id` are mandatory. Use UTC and `Z` for persisted data. Convert to a user's local zone only when rendering `aw history`; never persist a machine-local rendering into the authoritative journal.

For same-checkout concurrency, acquire a per-artifact lock before reading the Markdown revision and journal head. The package already has a cross-platform `filelock` abstraction in [`platform_lock.py` lines 1-18](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/platform_lock.py#L1-L18) and declares `filelock` as its only runtime dependency in [`pyproject.toml` lines 26-50](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/pyproject.toml#L26-L50). Reuse it rather than introducing another lock.

Write the new journal contents to a temporary file, flush and `fsync` it, atomically replace the journal, then update the Markdown through the same transaction. The current `artifact_core.atomic_write` already uses temp-plus-replace but does not `fsync`; see [`artifact_core.py` lines 118-132](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/artifact_core.py#L118-L132). For authoritative history, extend the durability contract or document that it protects against process interruption but not every power-loss scenario.

Because the operation changes two tracked files, use a small recovery journal under ignored `.aw/state/runtime/transactions/`. The repository already has the needed pattern: plan finalization locks, snapshots its owned files, checkpoints phases, rolls back pre-commit interruption, and reports an unknown outcome rather than guessing after an ambiguous commit. See [`ipd_lifecycle.py` lines 1815-1820](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/ipd_lifecycle.py#L1815-L1820) and [lines 1888-1960](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/ipd_lifecycle.py#L1888-L1960). The history design should reuse or generalize this machinery, not invent an unrelated best-effort dual write.

### Ordering becomes unambiguous by construction

For all new version-2 events, yes: order is unambiguous by construction.

The valid stream is the one contiguous chain where:

1. `seq` is exactly the previous sequence plus one;
2. `parent_event_id` equals the previous event's `event_id`;
3. the event's `from_status` equals the authoritative Markdown status at the previous revision;
4. the event's `to_status` equals the Markdown status at the new revision;
5. the Markdown `Revision` equals the journal head's `seq` after the transaction.

Two branches can both create sequence 8 from the same sequence-7 parent. Their UUIDs differ, but the duplicated sequence and shared parent prove a fork. The merge must not silently sort by timestamp. It should fail closed and require an explicit reconciliation that chooses or legally composes the transitions. This is preferable to hiding a same-artifact race.

Timestamps are never the sequencing authority. That eliminates both the day-granularity defect and the UTC-versus-local-date inversion. It also represents legitimate same-day round trips exactly, provided the lifecycle policy explicitly permits the relevant edge.

### Legacy history must not be given invented precision

The existing mixed inline records do not contain enough information to recover a universally correct order. Migration must preserve that uncertainty.

For each migrated artifact:

- preserve every raw legacy history record verbatim in `legacy` event records with its observed `YYYY-MM-DD`, original file ordinal, and `ordering_confidence` (`known`, `inferred-from-git`, or `unknown`);
- where Git history clearly shows when a line or status field was introduced, record that commit and use it as evidence, but do not assume every history line maps cleanly to one commit;
- create a version-2 `checkpoint` at sequence 0 that accepts the current inline metadata snapshot as the cutover state;
- chain all new typed events from that checkpoint;
- do not run forward-transition validation across unordered pre-checkpoint legacy records;
- retain the legacy raw text until a round-trip export proves no content was lost.

This preserves the past without pretending that rank sorting discovered facts that were never recorded. The existing 15 false lifecycle diagnostics should be replaced immediately by a dedicated legacy-order ambiguity finding or grandfathered pre-checkpoint status, while all new version-2 events remain fail-closed.

## Single-source-of-truth position

There should be one authority **per kind of fact**, not two competing copies of everything:

| Fact | Authority | Derived or cross-checked representation |
|---|---|---|
| Current status, scope, readiness, dependencies, gates, and provenance links | Markdown metadata block | Indices and attention views. |
| Historical event identity, order, actor, time, and transition details | Per-artifact JSONL journal | `aw history` human/JSON output; optional SQLite cache. |
| Narrative goal, plan, findings, and validation evidence | Markdown prose | Any generated summaries. |
| Global query/index state | Neither a hand-edited JSON nor SQLite authority | Recomputed from Markdown plus journals. |
| Local operational telemetry | Ignored `.aw/state/` data, if retained | None required. |

The typed transition event necessarily repeats the before/after status to describe what happened. That does not make it a second mutable current-status field. Operational reads use the Markdown status, while `aw check` requires the journal head and Markdown revision/status to agree before another lifecycle write or CI success.

Drift handling must be explicit:

- **Journal advanced, Markdown not advanced:** recover or roll back the interrupted transaction from its journal. Do not silently accept the event.
- **Markdown advanced, matching event absent:** fail `check.history-state-drift`. If Git proves an intentional hand edit, an explicit `aw history reconcile` appends a new reconciliation event with the evidence and advances the revision. Do not backdate or fabricate the missing original event.
- **Malformed journal line:** fail closed with its file and line number. Do not skip it.
- **Sequence gap, duplicate sequence, or parent fork:** fail closed. Repair requires an explicit merge/reconciliation event or choosing one branch and replaying the other legal transition.
- **Generated output drift:** regenerate from the authorities and compare exact bytes. `aw history --format json`, any committed summary view, and the optional SQLite index must have deterministic serialization and a `--check` mode. No "last writer wins" repair is acceptable.

If the project elects to retain a one-line inline "latest event" for convenience, make it a byte-reproducible projection of the journal head and state plainly that the journal wins. I do not recommend retaining it: `Status` and the event diff already provide the useful review context, while `aw attention` can read the journal directly.

## Effect on current consumers

### `IPD-S405` and terminal attribution

Replace the inline-text requirement with a version-aware rule:

- Version 1: retain today's inline `executed` check for compatibility.
- Version 2: require the journal head or a valid ancestor event to contain a typed `status` transition to `executed`, require `to_status == executed`, require the event actor to be the authorized finalizer, require a nonempty summary, and require the event revision to match the Markdown revision.

The current inline rule is at [`ipd_lint.py` lines 725-747](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/ipd_lint.py#L725-L747), and its "newest executed" attribution helper depends on top-down inline order at [lines 765-813](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/ipd_lint.py#L765-L813). Both should consume the typed journal through one shared history API.

This is stronger than the current rule. It validates event identity, parentage, actor, and typed transition rather than merely finding a plausible prose line anywhere in Markdown.

### `aw attention last_history_at`

For version 2, derive the field from the journal head's `occurred_at`, not from the last line in file order. The current contract explicitly uses the last inline record date in [`attention_contract.py` lines 448-462](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/attention_contract.py#L448-L462), even though plan writers now prepend. That rule is already inconsistent across artifact types.

Prefer renaming the machine field to `last_event_at` and returning the full UTC timestamp. If API compatibility requires `last_history_at`, keep the name temporarily but change and version its documented semantics. For legacy version-1 artifacts, continue returning the best available day or `null` with an explicit legacy-precision marker in JSON output.

### Human review and Git diff

A status change produces two small diffs in the same commit:

1. the artifact changes `Status` and `Revision`;
2. its journal gains one canonical JSON line.

This is still reviewable without running a tool. Add a diff driver or `aw history --git-diff` renderer only as an ergonomic enhancement, not as the only way to see state. Pre-commit and CI checks should require both paths when a managed state transition occurs.

## Comparison of realistic options

Token effects use the prompt's measurements because they include the maintainer's extra live plan. "Save 10.2%" means the history no longer enters context when an agent reads all plan Markdown. Actual savings vary by tokenizer and by whether an agent explicitly asks for history.

| Option | Token/context effect | Parse robustness | Concurrent-agent and Git merge behavior | Human diff legibility | Crash/partial-write safety | Migration cost | Assessment |
|---|---|---|---|---|---|---|---|
| **A. Status quo: all inline Markdown** | Saves nothing; approximately 403,671 estimated tool-owned tokens remain in the full corpus and history grows without bound. | Low. Bespoke regex plus mixed prose; sequence cannot be reconstructed. | Different artifacts usually isolate conflicts, but prepending and appending in the same section makes same-file merges and interpretation fragile. | Best single-file readability. | Fair for one Markdown file because many writers use atomic replace; no cross-file transaction. | None. | Reject. It already causes false CI failures and unbounded context growth. |
| **B. Inline front matter, history in the existing global sidecar** | Saves approximately 275,451 estimated tokens, or 10.2%. | Low to medium as implemented. JSON parses, but schema has no typed transitions, identity, or sequence and silently skips corruption. | Poor if tracked: all agents append at one EOF. Poor durability if ignored: other clones lose history. | Current state remains clear; full history is a separate diff only if tracked. | Poor as implemented: unlocked direct append, swallowed failures, and nontransactional dual writes. | Medium, perhaps 3-6 focused days to route plans and consumers, but more to make it authoritative. | Reject as a destination. Finishing only the stalled routing relocates the ordering bug and preserves larger correctness defects. |
| **C. All tool-owned metadata in per-artifact JSON/JSONL sidecars** | Nominally saves the full 14.9%, but agents often need to fetch the removed fields immediately. | High with a strict schema. | Good across different artifacts; same-artifact conflicts remain localized. | Poorer: a Markdown diff no longer shows whether a plan is approved, gated, or in scope. | Requires a two-file transaction for prose plus metadata and careful repair. | High. Every metadata parser, writer, template, and human workflow changes. | Reject for this repository. The additional token saving is not worth hiding high-value state. |
| **D. One tracked central append-only JSONL** | Saves 10.2% for history-only, up to 14.9% if all metadata moves. | Potentially high with the proposed schema, but a single damaged file affects all artifacts. | Worst Git hotspot. Independent appends to one EOF commonly conflict; same-checkout writers also require one global lock. | Moderate for history, poor for locating one artifact in a large diff. | Can be made process-safe with a lock and atomic rewrite, but one failure has repository-wide blast radius. | Medium. Existing code is a starting point, but its semantics need major changes. | Reject. The global file couples unrelated work and conflicts with the repository's concurrency model. |
| **E. SQLite source of truth plus generated views** | Excellent if agents read only Markdown prose; generated inline views may reintroduce the cost. | Excellent local schema, transactions, indexing, and query behavior. | Good for simultaneous local processes through SQLite locking; very poor as a Git-carried binary. Git cannot meaningfully line-merge or review database pages. | Poor unless generated text views are committed, which creates duplicated state and drift management. | Excellent database transaction safety; generated-file transaction still required. | Very high. Requires schema migrations, export/import, generated views, and binary-Git policy. | Reject as authority. Use only as a disposable cache derived from tracked text. |
| **F. Recommended hybrid: inline current state plus tracked per-artifact typed JSONL events; optional derived SQLite** | Saves approximately 275,451 estimated tokens, or 10.2%, while keeping agent-relevant fields inline. History is loaded only on demand. | High. Strict versioned JSON, typed transitions, sequence and parent checks; legacy uncertainty remains explicit. | Best fit. Unrelated artifacts touch unrelated files. A same-artifact fork is detected and must be reconciled. | High. Current state is in the Markdown diff and the event is a separate plain-text diff. | High when implemented with per-artifact locking, atomic replace/fsync, and the existing journaled transaction pattern. | Medium-high. Roughly 11-19 focused engineering days for a robust cutover. | Recommend. It balances context, correctness, Git, and human review rather than maximizing one metric. |

## Incremental migration path

The previous migration stalled because it treated plans as a special exclusion and left no enforced path to eliminate that exclusion. The new migration should make format version and compatibility explicit, make all new writes use one API, and ratchet the legacy population downward in CI.

### Phase 0: stop the false CI result without inventing history

1. Change `check.lifecycle-transition-invalid` so it does not apply a fixed-direction interpretation to unsequenced legacy histories.
2. Emit a separate `check.history-order-ambiguous` diagnostic for mixed/unsequenced legacy data, initially advisory or grandfathered.
3. Add tests that reproduce 15 current, 32 date-sort, and 3 rank-sort diagnostics so no future patch reintroduces inference disguised as ordering.
4. Resolve the lifecycle-policy inconsistency explicitly: define legal plan transition edges, including whether and how `approved` or `auto-approved` may return to `reviewed` for re-review.

This restores truthful CI quickly. It does not claim the legacy history is valid; it says the available record is insufficient to judge it.

### Phase 1: build one strict history abstraction

1. Define `aw.history/v2`, canonical serialization, strict diagnostics, and the per-artifact path function.
2. Add an `ArtifactHistory` API that reads version-2 JSONL or, for legacy version 1, the bounded inline section.
3. Add per-artifact locking, revision/parent validation, atomic write with fsync, and transaction recovery.
4. Separate durable lifecycle events from the current best-effort local rename/activity ledger.
5. Make missing, malformed, duplicate, gapped, or forked version-2 history a fail-closed error. Remove blanket exception swallowing on authoritative writes.

No caller should parse `## Workflow history` directly after this phase. The 19 modules may still contain help text, but runtime behavior must go through the one abstraction.

### Phase 2: route every writer before slimming more files

1. Route plan, spec, backlog, release, and other lifecycle writers through the shared transaction API.
2. New artifacts are born with `Metadata-Version: 2`, a revision, and a per-artifact journal. They never receive an inline history section.
3. A version-1 artifact stays readable and writable through compatibility code. On its next managed state transition, the tool may offer or perform an atomic migrate-then-transition operation.
4. Update the untooled-status detector to require a paired journal event/revision change rather than a plausible prose line. The current textual gate admits a hand edit that also fabricates a line, as its own documentation acknowledges in [`status_untooled_gate.py` lines 9-20](https://github.com/fariello/agent-workflows/blob/4763eb8de8784aff4547015efe68546c11ab0f92/agent_workflows/hooks/status_untooled_gate.py#L9-L20).

This closes the hole that caused the prior effort to stall: once all writers can emit version 2, the largest tree is no longer excluded by design.

### Phase 3: migrate safely in bounded batches

1. On the maintainer's authoritative checkout, first export and preserve the ignored 128-record local sidecar before changing anything. A clean clone does not have those records.
2. Run a dry migration that reports counts by artifact, duplicates, malformed records, unresolvable IDs, inferred order, and unknown order. Write nothing in preview mode.
3. Migrate terminal plans in small deterministic batches first. They are numerous but not actively changing. Then migrate active sets one set at a time under locks.
4. For each artifact, write its journal and stripped Markdown through one recovery transaction; re-read both; verify every legacy raw line survived; verify the current metadata is byte-identical except for format/revision fields and removal of the history section.
5. Commit each batch with only that batch's Markdown and journal paths. Do not create one 500-file conflict window unless there is a compelling release-management reason.
6. Track migration progress by scanning `Metadata-Version`, not by hand-maintaining a central progress file.

### Phase 4: dual-version checks and a ratchet

1. `IPD-S405`, attribution, attention, readiness, doctor, and lifecycle checks dispatch by metadata version.
2. Add a CI ratchet: no new version-1 artifact, and legacy count must never exceed a committed ceiling. Lower the ceiling with each batch until it reaches zero.
3. Make a version-2 artifact with inline history a drift finding. Make a version-2 journal that is ignored or untracked a fail-closed finding.
4. Keep the version-1 reader until the last migration commit is present in all supported branches, then remove legacy writes first and legacy reads in a later cleanup.

The ratchet and "new artifacts are v2" rule are what prevent a second stall. Progress can pause without regression, and ongoing agents do not create more legacy debt.

### Phase 5: deterministic derived views and optional cache

1. Change `aw history <id6>` to render from the per-artifact journal in deterministic sequence order.
2. Update `aw attention` to read the typed head event and expose full UTC precision.
3. If global query time becomes material, build `.aw/state/history.sqlite3` as an ignored cache. Include a schema/input digest and rebuild it when stale. Deleting it must change no result except performance.
4. Remove or relocate the old ignored `.aw/records/history.jsonl` only after its durable lifecycle records have been imported and verified. Never silently discard it.

## Migration effort estimate

This is a planning estimate, not a measured implementation result. The largest uncertainty is how much of the existing finalization transaction can be generalized without destabilizing active runner work.

| Work package | Estimated focused engineering time |
|---|---:|
| Schema, canonical JSONL parser/writer, paths, strict diagnostics, unit tests | 2-3 days |
| Locking, revision/parent rules, atomic/fsync write, two-file recovery transaction | 2-4 days |
| Shared reader facade and migration of the 19 reference modules plus related tests/help | 3-5 days |
| Legacy importer, Git-assisted evidence, raw-line preservation, dry-run/report, batch migration | 2-4 days |
| CI ratchet, IPD-S405/attention/untooled-gate cutover, documentation and cleanup | 2-3 days |
| **Total** | **11-19 focused engineering days** |

Expect roughly 15-25 runtime/test/documentation files to change before corpus migration, plus the generated per-artifact journals and Markdown deletions. The estimate should carry at least a 50% uncertainty band until a vertical slice migrates one spec, one backlog item, one pending plan, and one executed plan through crash and merge tests.

A narrow "finish the current plan sidecar migration" could be done faster, perhaps 3-6 focused days, but that estimate excludes the work needed to make the result authoritative. It would retain the ignored-file data-loss problem, untyped events, ambiguous order, global merge hotspot, swallowed writes, and nontransactional divergence. It is therefore false economy.

## What I would not do

1. **Do not normalize 482 Markdown histories and call the bug fixed.** That is a large rewrite, loses useful blame locality, and remains vulnerable until every writer uses the same convention. It also cannot recover true order inside same-day mixed blocks.
2. **Do not sort legacy events by date and lifecycle rank.** Dates have day precision, and rank sorting rewrites evidence to fit the validator. It cannot truthfully represent rollback, re-review, or two same-status review rounds.
3. **Do not merely route plans into the existing ignored global JSONL.** A fresh clone would lose the full plan history just as it currently loses the full spec/backlog history. The existing schema still cannot validate a lifecycle sequence.
4. **Do not make a tracked central JSONL the authority.** It creates one Git conflict hotspot and repository-wide corruption blast radius. The current claim that append-only lines rarely conflict is not borne out by a simple two-branch append trial.
5. **Do not make SQLite the tracked source of truth.** SQLite is excellent for local transactions and queries, but a binary database is poorly matched to Git review, line merges, blame, and hand repair. Use it only as a disposable derived index.
6. **Do not move all front matter out of Markdown.** The extra nominal token saving is small relative to the usability and safety cost. Much of that block is agent-relevant state, not dead administrative weight.
7. **Do not keep duplicated mutable status in Markdown and a sidecar with an unspecified winner.** Define current snapshot and event history as separate authorities, bind them with revision/parent invariants, and fail on drift.
8. **Do not silently skip malformed authoritative records or swallow write failures.** An audit record that can disappear without failing the state transition is not an audit record.
9. **Do not invent precise timestamps or causal order for legacy lines.** Preserve their raw dates and uncertainty, establish a trusted cutover checkpoint, and guarantee strict sequencing only from that point forward.
10. **Do not mix durable lifecycle audit with optional local telemetry.** If rename/activity logging remains best-effort and ignored, keep it in `.aw/state/`; do not let it determine artifact correctness or share a file with the Git-carried lifecycle source.

## Acceptance criteria for the recommended design

The design is ready to adopt when a vertical slice proves all of the following:

- Reading an ordinary plan Markdown no longer includes its historical narrative, while status, scope, dependencies, readiness, and gates remain visible.
- Two different artifacts can transition concurrently without touching the same tracked history path.
- Two stale writers targeting the same artifact cannot both advance the same revision.
- A same-day `reviewed -> approved -> reviewed -> approved` sequence is represented exactly when those edges are legal.
- UTC persisted timestamps never depend on the workstation's local date; local rendering is display-only.
- A crash after either tracked-file write is detected and recoverable through the transaction journal.
- A malformed JSONL line, sequence gap, duplicate sequence, wrong parent, wrong artifact ID, or Markdown/journal revision mismatch fails closed with a stable rule ID.
- `IPD-S405` and terminal attribution are stronger on version 2 than today and no longer depend on prose order.
- `aw attention` derives the last event from the typed journal head, not file position or date sorting.
- Every legacy raw history record and every available record from the maintainer's ignored sidecar is preserved or explicitly reported as unresolvable; no migration mode silently drops data.
- Generated history views and any SQLite cache are reproducible from tracked authorities, with drift detectable by `--check`.
- CI prevents new version-1 artifacts and monotonically ratchets the remaining legacy count to zero.

## Bottom line

The correct unit of separation is not "all metadata." It is the unbounded event history. Keep the bounded, decision-relevant current snapshot with the Markdown; store typed history in tracked per-artifact JSONL; use explicit sequence and parent identity rather than timestamps for order; and treat SQLite only as a rebuildable cache. This removes the dominant context waste, preserves useful Git diffs, localizes concurrent changes, and fixes the ordering defect structurally for every event after a truthful legacy cutover.
