# IPD: Freeze the resolved model identity and rate card into the run record so a recorded cost can be attributed and recomputed

- Date: 2026-09-08
- Kind: child
- Concern: The run record captures per-step COST but neither the MODEL that incurred it nor the RATE CARD that priced it, so a recorded dollar figure cannot be attributed to a model or recomputed from its inputs. Three gaps, each re-measured at HEAD `44d4950d` across all 135 run directories rather than trusted from the backlog item.
  GAP 1, THE RUN-LEVEL MODEL, PARTLY CLOSED SINCE THE ITEM WAS FILED. `options.model` is set in only 5 of 135 runs, so the item's "null on every run" is now FALSE in the letter and TRUE in substance: the 5 are the ones where an operator passed `--model` explicitly, and the other 130 record `null` because the model comes from the host's own config. What HAS landed is the provenance object: 33 of 135 runs carry `options.launch_profile` (`oc_runipd.launch_profile_record`, `:2740`, shipped by `runprofile` Order 03 `3cm15q`), and it records `model`, `variant`, `agent`, a `config_digest`, and a per-field `provenance` map. In all 33 the provenance reads `{"model": "host-default", ...}` unless `--model` was passed, and `PROVENANCE_HOST_DEFAULT` is documented as "nothing supplied it; pass no argument" (`runner_profiles.py:378`). So the record now says HONESTLY that it does not know the model, which is a real improvement and precisely what still needs closing: `host-default` names the gap instead of filling it.
  GAP 2, THE PER-STEP MODEL, ENTIRELY OPEN. The per-step records in `sessions/*.jsonl` carry `part.cost` and `part.tokens{input,output,reasoning,cache{read,write}}` but NO model id. RE-MEASURED across every session log in the repository: 28158 cost-bearing steps, 0 carrying a `modelID`/`modelId`/`model` key, 0 distinct model ids. The item measured 9757 steps; the corpus has since tripled and the ratio is unchanged at exactly zero.
  GAP 3, THE RATE CARD, ENTIRELY OPEN AND NOT IN THE REPOSITORY AT ALL. The card lives in the user's host config, which `aw oc update-models` MUTATES from a LiteLLM admin endpoint (`oc_models.py`, `sync_provider` `:607`, `per_million` `:501`), and `resolve_config_path` (`:96`) resolves that file the way OpenCode itself does. That config demonstrably changes: research `x0spmh` records the card being CORRECTED mid-history from `input 5.00 / output 25.00, cache_read UNPRICED` to `5.50 / 27.50 / 0.55 / 6.875`, which makes Aug 24 and Aug 29 dollar totals NOT comparable and makes an Aug 24 `cache_read = $0` a CONFIG ARTIFACT rather than evidence that cache reads were free. Nothing in any run record lets a reader detect which regime priced it.
  THE CONSEQUENCE IS AN UNANSWERABLE QUESTION, NOT A COSMETIC GAP. Asked "is Opus 5 a better verifier than 4.8", the only available attribution was grepping model strings out of run directories, and every occurrence is inside a shell command an AGENT typed (e.g. an `aw ipd finalize ... --actor "opencode <model>"`), so per-model attribution rests on agent PROSE, which this framework elsewhere insists is never authority (research `ig9bai`). One run contains BOTH an `opus-4.8` and an `opus-5` string, so even the reconstruction is ambiguous.
- Scope: Record, per RUN, the RESOLVED model identity and the RESOLVED rate card in effect at launch, with a digest so a later host-config edit is detectable, and make cost views read the recorded card rather than the current one. EXCLUDES per-STEP model attribution, which no host currently emits (see OQ-01 and the deferred section); excludes any analytics, statistics, taxonomy, pricing-era arithmetic, SPA, export, or query surface, ALL of which belong to the `runanalytics` Set; excludes changing what any model is or how it is chosen (`runprofile`).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/oc_models.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_oc_models.py
- Item-Dependencies: none
- Status: to-review
- Set: runverdict
- Order: 7
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: w33lrl
- Blocks-Release: next
- From-Backlog: vlf75p

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `vlf75p` as a NARROWED plan; the item carries `- Blocks-Release: next` and this plan inherits that gate. TWO NARROWINGS, both recorded in the item itself so no reader is misled.
  FIRST NARROWING, PARTIAL OBSOLESCENCE FROM SHIPPED WORK. The item's gap 1 says `options.model` is "null on every run". Re-measured: 5 of 135 runs have it set, and more importantly `runprofile` Order 03 (`3cm15q`, executed) shipped `launch_profile_record` (`oc_runipd.py:2740`) which now freezes a provenance object into 33 of 135 runs carrying `model`, `variant`, `agent`, `config_digest` and a per-field `provenance` map. So the RECORD-A-PROVENANCE-OBJECT half of gap 1 is DONE and must not be rebuilt; what survives is that its `model` reads `host-default` (`runner_profiles.py:378`, "nothing supplied it; pass no argument") because nothing resolves the host's own default. This plan fills that value; it does not re-invent the container. Also noted: agy has ZERO profile integration (`runner_profiles`, `resolve_launch_profile` and `launch_profile` all grep to nothing in `agy_runipd.py`), which pending plan `kgpptv` records as a measured host asymmetry, so parity here is not free and OQ-02 owns it.
  SECOND NARROWING, OVERLAP WITH THE PENDING `runanalytics` SET, which is the expensive mistake this note exists to prevent. That Set (11 plans, `to-review`/`reviewed`, orchestrator `5lxvl3`) owns everything DOWNSTREAM of the record. Specifically: `5f2h8i` (Order 04) E-01/E-02 already declare that telemetry "records resolved run/set/IPD/attempt/phase/model/provider/variant metadata" per invocation and that "the execution ID, attempt, phase, start/end times, model identity, and node pseudonym must be recorded per file and must not be inferred later from a single run-level snapshot"; `aflsz3` (Order 06) E-02 owns "effective-dated pricing" with "price schedules carry provider/model/variant, input/output/cache rates, currency, effective interval, and source/version", plus the explicit convention "Model prices changed over time. A timeless price map would rewrite history and is forbidden"; and `8hald1` (Order 05) owns the normalized fact schema carrying "runner/model/variant" and "pricing-key" facts. THEREFORE this plan does NOT graduate the item's fix-sketch clauses about per-TURN capture, effective-dated schedules, pooled-aggregate exclusion, or `aw runs` cost views computing from a card, and does NOT graduate its test (b) cost-recomputation-to-the-cent, test (d) pooled-aggregate exclusion, or test (e) per-model aggregation. Those are `aflsz3`'s and `8hald1`'s by declaration. What this plan graduates is the ONE thing the `runanalytics` Set cannot do for itself: those plans consume a model identity and a rate card from the run record, and TODAY THE RUN RECORD CONTAINS NEITHER, so a telemetry integration that "records resolved model" would record `host-default` and a pricing engine would have no in-repo card to be effective-dated. This plan is the PRODUCER; that Set is the CONSUMER. The boundary is stated in the deferred section and pinned by OQ-03.
  THE ITEM'S REMAINING CLAIMS ALL HELD ON RE-MEASUREMENT: 28158 cost-bearing steps with ZERO model ids (the item measured 9757; the corpus tripled and the ratio is still exactly zero), the card absent from the repository, and `aw oc update-models` demonstrably mutating it.

## Goal

Make a run record say which model incurred its cost and at what prices, so the figure can be attributed and recomputed, and so a later host-config edit cannot silently reprice history.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: resolve the model the host will actually use

- [ ] E-01 RESOLVE THE HOST'S OWN DEFAULT MODEL AND RECORD IT, filling the value that today reads `host-default`. Do NOT build a new provenance container: `launch_profile_record` (`oc_runipd.py:2740`) already exists, already freezes `model`/`variant`/`agent`/`config_digest`/`provenance`, and its docstring states its purpose ("Records WHICH configuration produced this run's launch and WHERE each field came from"). Add the resolved host default as an additional recorded field with its own provenance value; do not overwrite `model`, whose `host-default` provenance is a TRUE statement about the flag and must stay true.
  READ THE HOST CONFIG THROUGH THE EXISTING NO-SECRET READER. `oc_models.resolve_config_path` (`:96`) resolves the config "the way OpenCode does" (`$OPENCODE_CONFIG`, then a project `opencode.json`/`.jsonc` walking up, then `$XDG_CONFIG_HOME`, then `~/.config`), and `models_from_config` (`:301`) reads ONLY the per-provider model keys with the documented guarantee that "It never looks at a provider's options block, credential value, or headers, so no secret can reach the caller." USE THAT GUARANTEE. Writing a second config reader here would be the exact way a credential reaches a run record.
  RECORD AN UNRESOLVABLE MODEL AS A NAMED UNKNOWN, NEVER OMIT IT. The item requires this explicitly, and `runner_profiles.PROVENANCE_VALUES` (`:380`) is already a closed enum, so an added provenance value must be admitted there rather than smuggled in as a free string. A `.jsonc` config is UNPARSEABLE BY DESIGN (stdlib json cannot preserve comments, `_classify_target` `:138` marks it unwritable) and `catalog_from_config` returns a documented `CATALOG_UNPARSEABLE` reason for it; that is a real and reachable unknown, not a hypothetical.
  DO NOT LEAK A LOCAL PATH INTO THE RECORD WITHOUT CHECKING. `launch_profile_record` already stores `config_source`, and the 33 live examples contain an absolute maintainer home path in it. The orchestrator of the `runanalytics` Set records that every recent `state.json` already carries an absolute maintainer home path in `repo` and `driver.path`, so this is a pre-existing condition rather than one this plan creates; but run `aw sanitize --agent` before and after and do not make it worse. If the resolved card or model carries a path, record a digest or a basename rather than the path.
  - Depends on: none
  - Expected outcome: the run record names the model the host will actually use, or a NAMED unknown with a provenance value admitted to the closed enum; the host config is read only through `oc_models`' no-secret readers; `aw sanitize --agent` is no worse than before.
  - Execution state: pending

### Task group 2: freeze the card that priced the run

- [ ] E-02 SNAPSHOT THE RESOLVED RATE CARD AT LAUNCH, with its four components (input, output, cache_read, cache_write), the model it applies to, and a DIGEST, and record explicitly that it is a LAUNCH-TIME SNAPSHOT rather than a per-step observation. The item asks for exactly this and for the snapshot to be labelled as such.
  REUSE `oc_models`' PRICE VOCABULARY, do not invent a second unit. `per_million` (`:501`) converts a per-token cost to dollars per million and REFUSES untrusted input (a bool, string, None, or non-positive number yields `None` rather than a bogus price), with the documented reason that "The gateway response is untrusted input". Whatever this plan records must use one unit consistently and must state which; recording per-token and per-million values under similar names is how a 1000000x error enters a cost report.
  A MISSING OR PARTIAL CARD IS A NAMED UNKNOWN, NOT A ZERO. This is the highest-value single instruction in this plan, because research `x0spmh` documents the exact trap: the pre-correction card left `cache_read` UNPRICED, and the resulting `cache_read = $0` was read as evidence that cache reads were free when in fact 73.9% of a $16.41 turn was cache reads. A zero and an absence must be distinguishable in the record.
  THE DIGEST IS WHAT MAKES A LATER EDIT DETECTABLE, and it is the reason this is not merely a copy. `aw oc update-models` mutates the host config from a LiteLLM admin endpoint (`oc_models.sync_provider` `:607`), and the maintainer's config has multiple timestamped `.bak` siblings, so the card demonstrably changes between runs. `launch_profile_record` already carries a `config_digest` for the PROFILE store; decide whether the card's digest belongs in that same field or a distinct one, and say why. Do NOT overload one digest to mean two files.
  - Depends on: E-01
  - Expected outcome: the run record carries the four-component card, the model it applies to, a digest, and an explicit launch-time-snapshot label; units stated and consistent; a missing component recorded as a named unknown distinguishable from zero; the digest's scope decided and justified.
  - Execution state: pending

- [ ] E-03 MAKE THE RECORDED CARD THE AUTHORITY FOR THAT RUN'S REPORTED COST, so a host-config change after a run does NOT change that run's reported figure. This is the item's test (c) and it is the property that makes the whole record worth writing.
  DO NOT COMPUTE COSTS HERE. The recorded `part.cost` values are what the host reported and remain the primary figure; this item is about NOT SUBSTITUTING a current price for a historical one. Any RECOMPUTATION from tokens times card is `aflsz3`'s E-02 (effective-dated pricing) and `8hald1`'s normalized facts, which explicitly separate "recorded cost" from "estimated cost". Adding a second cost computation here would fork exactly the distinction that Set exists to maintain.
  A RUN WITHOUT A RECORDED CARD MUST NOT SILENTLY BORROW THE CURRENT ONE. Every run created before this plan lands has no card, and that is the majority. Such a run must report its recorded cost with the card marked ABSENT, never with today's prices, because that is the pooled-comparison error `x0spmh` documents.
  - Depends on: E-02
  - Expected outcome: a run's reported cost is unaffected by a host-config edit made after it; a run with no recorded card reports the card as ABSENT rather than borrowing the current one; no second cost computation is introduced.
  - Execution state: pending

### Task group 3: parity, proof, and the consumer boundary

- [ ] E-04 DECIDE AND IMPLEMENT THE AGY POSITION, then state it honestly. Agy has ZERO profile integration: `runner_profiles`, `resolve_launch_profile` and `launch_profile` all grep to NOTHING in `agy_runipd.py`, a measured asymmetry pending plan `kgpptv` already records. So "both hosts" is not free here as it is for most runner work.
  SITE ANY SHARED SYMBOL IN `runner_shared.py`, NEVER IN `oc_runipd.py`. `agy_runipd` already imports 47 names from `oc_runipd` (AST-measured 2026-09-08) and zero flow back; adding to oc for agy to import would make it 48 and deepen the layering defect backlog `cnwy8g` owns.
  IF AGY CANNOT RECORD A CARD, RECORD THAT IT CANNOT, rather than leaving its runs indistinguishable from an unresolvable-card oc run. Also relevant and measured by the `runanalytics` orchestrator: this checkout holds ZERO agy runs (120 `oc_runipd.py`, 13 legacy `runipd.py`, 2 `ipdrunner.py`), so any agy evidence is necessarily synthetic and must be labelled as such rather than presented as observed.
  - Depends on: E-02
  - Expected outcome: the agy position decided, implemented, and stated; a shared symbol lives in `runner_shared`; an agy run that cannot resolve a card is distinguishable from an oc run that failed to; agy evidence labelled synthetic.
  - Execution state: pending

- [ ] E-05 PROVE THE RECORD ON REAL AND SYNTHETIC INPUT, from FIXTURES. `.aw/records/runs/` is gitignored and roughly 32 tests fail inside a lane worktree because several read live run state, so a test built on the live corpus passes here and fails in isolation.
  COVER THE UNKNOWN PATHS, WHICH ARE THE REACHABLE ONES: no host config at all (`resolve_config_path` returns `None`, `CATALOG_NO_CONFIG`); a `.jsonc` config (unparseable by design, `CATALOG_UNPARSEABLE`); a config with a model but no `cost` block; a card with `cache_read` absent (the `x0spmh` trap); and a card whose value is a string or negative (which `per_million` already refuses). Assert the record distinguishes each from a resolved card AND from zero.
  ASSERT THE 130 CARD-LESS HISTORICAL RUNS STILL READ HONESTLY. The record change must not make an existing run look like it has a card. Use a fixture shaped like a real pre-change `state.json`.
  - Depends on: E-03, E-04
  - Expected outcome: fixture-driven tests for every unknown path and for the historical card-less shape; each unknown distinguishable from a resolved card and from zero; no test reads the gitignored live run tree.
  - Execution state: pending

- [ ] E-06 PIN THE CONSUMER BOUNDARY WITH THE `runanalytics` SET, in the code and in a test, so the two do not build the same thing twice. That Set's plans DECLARE that they record model identity per invocation (`5f2h8i` E-01/E-02) and own effective-dated price schedules (`aflsz3` E-02) and the normalized pricing-key facts (`8hald1` E-02). This plan's output is their INPUT.
  READ THOSE THREE PLANS' STATUSES ON DISK AT EXECUTION TIME and record what you found. If any has EXECUTED, check whether it already wrote a model/card field and, if so, CONSUME it rather than adding a parallel one; a second field naming the same fact is the failure mode this item exists inside a Set to avoid. If none has, this plan's field is the one they will consume, and its NAME and UNITS become a contract; state them explicitly so a later plan binds to them rather than guessing.
  DO NOT IMPLEMENT AN EFFECTIVE-DATED SCHEDULE, a pooled-aggregate exclusion rule, a per-model comparison, or a cost recomputation. All four are declared deliverables of that Set. This item's job is to make its declarations satisfiable, not to pre-empt them.
  - Depends on: E-05
  - Expected outcome: the three plans' statuses read and pasted; the field name and units stated as a contract; no effective-dated schedule, pooled-exclusion rule, per-model comparison, or cost recomputation implemented here; a test or comment pinning the boundary.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PROVENANCE CONTAINER ALREADY EXISTS AND MUST BE EXTENDED, NOT REPLACED. `launch_profile_record` (`oc_runipd.py:2740`) freezes `requested`/`applied`/`runner`/`config_source`/`config_present`/`config_digest`/`model`/`variant`/`agent`/`provenance`, and its docstring states it "Contains NO credentials: only the model/variant/agent identifiers, the profile names, and the store path", because `runner_profiles` stores no secrets by construction. Preserve that property.
- `PROVENANCE_VALUES` IS A CLOSED ENUM (`runner_profiles.py:380`), so a new provenance value must be admitted there. `PROVENANCE_HOST_DEFAULT` means "nothing supplied it; pass no argument" (`:378`), which is why the current record honestly says it does not know.
- `oc_models` OWNS HOST-CONFIG READING AND HAS THE NO-SECRET GUARANTEE. `resolve_config_path` (`:96`) resolves it the way OpenCode does; `models_from_config` (`:301`) "never looks at a provider's options block, credential value, or headers"; `per_million` (`:501`) refuses untrusted input rather than coercing a bogus price; `_classify_target` (`:138`) marks a `.jsonc` config unwritable because comments cannot be round-tripped. Reuse all four rather than reading the config a second way.
- THE CARD DEMONSTRABLY CHANGES. `sync_provider` (`:607`) rewrites prices from a LiteLLM admin endpoint and computes `added`/`removed`/`changed` sets, so the mutation is first-class behavior rather than an accident. This is why a digest, not a copy, is what makes a later edit detectable.
- A ZERO AND AN ABSENCE ARE DIFFERENT, and this repository has already been misled by conflating them: research `x0spmh` records that the pre-correction card left `cache_read` unpriced, making a `$0` look like free cache reads when 73.9% of a $16.41 turn was cache reads.
- AGENT PROSE IS NEVER AUTHORITY (research `ig9bai`), which is exactly why grepping a model name out of an agent-typed shell command is not attribution.
- THE `runanalytics` SET OWNS EVERYTHING DOWNSTREAM. Its convention is stated plainly in `aflsz3`: "Model prices changed over time. A timeless price map would rewrite history and is forbidden." This plan produces the per-run truth that convention needs.
- THE IMPORT DIRECTION IS ONE-WAY: `agy_runipd` imports 47 names from `oc_runipd`; `oc_runipd` imports zero from agy. Shared symbols go in `runner_shared`.
- AGY HAS NO PROFILE INTEGRATION AT ALL, and this checkout has ZERO agy runs, so agy evidence is synthetic by necessity.
- `.aw/records/runs/` IS GITIGNORED. Use fixtures. Suite bare: `python3 -m pytest`; measure the baseline in the executing worktree and compare failing NODE IDS, never totals (a bare run on main is `1 failed, 5648 passed`, the known `tests/test_orchestrator_retirement.py` failure).

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | PARTLY OBSOLETE | `oc_runipd.py:2740`, `:3045` | The item says `options.model` is null on EVERY run; it is set in 5 of 135, and `launch_profile_record` now freezes a full provenance object into 33 of 135. So the CONTAINER half of gap 1 shipped with `runprofile` `3cm15q` and must not be rebuilt. | scanned all 135 `state.json`: 5 with `options.model`, 33 with `options.launch_profile` |
| F-2 | HIGH | `runner_profiles.py:378` | What survives of gap 1: the recorded `model` reads `host-default` ("nothing supplied it; pass no argument") in every profile-bearing run where `--model` was not passed. The record honestly names the gap instead of filling it. | read all 33 `launch_profile` objects; provenance `model` is `host-default` except where explicit |
| F-3 | HIGH | `sessions/*.jsonl` | Per-step model attribution is entirely absent: 28158 cost-bearing steps, 0 with any model key, 0 distinct model ids. The item measured 9757; the corpus tripled and the ratio is still exactly zero. | walked every session log, parsed every `part` with a `cost` |
| F-4 | HIGH | `oc_models.py:96`, `:607` | The rate card is not in the repository at all; it lives in the host config, which `aw oc update-models` mutates from a LiteLLM endpoint. | source read; the maintainer's config has multiple timestamped `.bak` siblings |
| F-5 | HIGH | research `x0spmh` | The card was corrected mid-history from `5.00/25.00, cache_read UNPRICED` to `5.50/27.50/0.55/6.875`, so pooled dollar comparisons across that boundary are invalid and an Aug 24 `cache_read = $0` is a config artifact. Cache reads were 73.9% of a $16.41 turn. | the research record's measured reconstruction |
| F-6 | OVERLAP | `5f2h8i` E-01/E-02, `aflsz3` E-02, `8hald1` E-02 | The pending `runanalytics` Set DECLARES per-invocation model metadata, effective-dated price schedules with source/version and effective intervals, and normalized pricing-key facts. Those are its deliverables, not this plan's; but they CONSUME a record that today contains neither a model nor a card. | read those three plans' E-items and conventions |
| F-7 | MED | `agy_runipd.py` | Agy has ZERO profile integration (`runner_profiles`, `resolve_launch_profile`, `launch_profile` all grep to nothing), and this checkout holds ZERO agy runs, so parity is not free and agy evidence is synthetic. | grep; the `runanalytics` orchestrator's measured run-generation census |
| F-8 | MED | `oc_models.py:301`, `:501`, `:138` | The no-secret reader, the untrusted-price refusal, and the `.jsonc`-unwritable classification already exist, so both the security property and the unknown paths are established rather than needing invention. | source read of the three docstrings |
| F-9 | LOW | 33 `launch_profile` objects | `config_source` already records an absolute maintainer home path, and the `runanalytics` orchestrator measured the same in `repo` and `driver.path`. Pre-existing, not created here, but do not make it worse. | read the live objects; run `aw sanitize --agent` |

## Proposed changes (ordered, validatable)

1. E-01 fills the host-default model value through `oc_models`' no-secret readers, extending the existing provenance container and admitting any new provenance value to its closed enum.
2. E-02 snapshots the four-component card with its digest and an explicit launch-time label, reusing `oc_models`' price vocabulary and distinguishing a missing component from zero.
3. E-03 makes the recorded card authoritative for that run's reported cost, without introducing a second cost computation.
4. E-04 decides and states the agy position, siting any shared symbol in `runner_shared`.
5. E-05 proves every unknown path and the historical card-less shape from fixtures.
6. E-06 pins the producer/consumer boundary with the `runanalytics` Set from those plans' on-disk statuses.

## Deferred / out of scope (with reason)

- NOT GRADUATED AS ALREADY SHIPPED, and recorded in the backlog item rather than only here: the RECORD-A-PROVENANCE-OBJECT half of the item's gap 1. `runprofile` Order 03 (`3cm15q`, executed) shipped `launch_profile_record` with `model`/`variant`/`agent`/`config_digest`/`provenance`, present in 33 of 135 runs. This plan extends it; rebuilding it would duplicate an executed plan's deliverable.
- NOT GRADUATED AS OWNED BY THE PENDING `runanalytics` SET, with the owner named per clause so nothing is silently dropped: EFFECTIVE-DATED PRICE SCHEDULES with currency, effective intervals and source/version (`aflsz3` E-02); COST RECOMPUTATION from tokens times card and the recorded-versus-estimated split (`aflsz3` E-02, `8hald1` E-02); POOLED-AGGREGATE EXCLUSION of unknown-card runs (`aflsz3` E-02's missingness and confidence handling); PER-MODEL AGGREGATION and model comparison with price-era stratification (`aflsz3`'s required analysis 12); PER-TURN and per-attempt model capture (`5f2h8i` E-01/E-02, which explicitly requires per-file identity "not inferred later from a single run-level snapshot"); and any `aw runs` cost VIEW change (`mm5p3v` Order 08, plus spec `25kzda`'s fixed `aw runs` leaf table). The item's tests (b), (d) and (e) belong to those plans by the same reasoning. This plan is the producer they consume.
- PER-STEP MODEL ATTRIBUTION IN `sessions/*.jsonl`. OQ-01. Not graduated because no host currently emits it: 28158 of 28158 cost-bearing steps carry no model key, and the item's own fix sketch says to "Prefer capturing what the host reports per step IF it can be made to emit it; otherwise snapshot at launch". This plan does the otherwise. Making the host emit it is an upstream question, and `5f2h8i` separately owns per-invocation telemetry.
- CHANGING WHICH MODEL IS USED, or per-role model routing. `runprofile` owns that (`3cm15q` executed, `kgpptv` pending for the verifier turn).
- AUTOMATIC PRICE SCRAPING. `aflsz3` excludes it explicitly, and `aw oc update-models` already exists as a deliberate operator action. This plan reads what is configured; it does not fetch.
- REPAIRING THE HISTORICAL RECORD. The 130 card-less runs stay card-less and must READ as such (E-03); back-filling a card onto them from today's config is precisely the history-rewriting `aflsz3` forbids.

## Scope check

- Over-scope: `oc_models.py` is in scope ONLY to expose or reuse the existing readers if a small accessor is genuinely needed; do NOT change `sync_provider`, the write path, the atomic write, or the backup behavior. `runner_shared.py` is in scope only to hold a shared symbol. Do NOT touch `run_viewer.py` or any `aw runs` view.
- Under-scope: stated rather than left as `none`. After this plan a run knows its model and card, but nothing yet RECOMPUTES a cost, stratifies by price era, excludes unknown-card runs from an aggregate, or attributes a single STEP to a model. Each is named above with its owner.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. Fixtures for every run-record shape; never the gitignored live tree. `tests/test_oc_models.py` is where config-reading cases belong, and its existing no-secret assertions must keep passing untouched. Run `aw sanitize --agent` before and after and paste both, since this plan writes host-derived values into a tracked-adjacent record.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, `- Status: approved`) §5.6 fixes the machine-output shape for a final item and does NOT include a model or a card field, and its `aw runs` leaf table is what the `runanalytics` orchestrator records Orders 08 and 09 as owing a DECLARED amendment for. THIS PLAN ADDS TO `state.json`'s `options`, which §5.6 does not enumerate, so no amendment is expected. VERIFY THAT BY READING RATHER THAN ASSUMING: if §5.6's per-item JSON or §7's ledger schema is read as a CLOSED shape, adding a field is an amendment and the spec file must be declared in `- Scope-Paths:` before execution, because the runners announce declared spec edits before a run starts and the finalize scope gate reconciles declared against actual. Report which you found.
Do NOT edit §4.2's finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Can the host be made to emit a per-step model id, and if so does that supersede the launch snapshot?

- Blocking: no
- Status: open
- Owner: this plan's executor for the measurement, the maintainer for any upstream request
- Resolution or deferral rationale: NOT blocking, because the item's own fix sketch prescribes the fallback this plan implements ("otherwise snapshot at launch and record that it is a launch-time snapshot"), so the plan is complete without an answer. Measured: 28158 of 28158 cost-bearing steps carry no model key, so the answer today is no. It matters because a launch snapshot is WRONG for a run whose verifier turn uses a different model, which pending plan `kgpptv` is specifically designed to enable; once that lands, one run legitimately has two models and a single run-level field cannot express it. Record that interaction rather than leaving it for a reader to discover, and note that `5f2h8i` E-01 separately declares per-invocation model metadata, so the eventual home may be there.

### OQ-02: Does agy record a card in this plan, or record that it cannot?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer if agy profile integration is required
- Resolution or deferral rationale: NOT blocking, because E-04 requires the position be DECIDED and STATED either way, and an honest "cannot resolve" record is strictly better than silence. The measured constraint: agy has zero profile integration and this checkout has zero agy runs, so building it here would mean implementing profile support for a host with no observed usage, inside a plan about cost attribution. The likely right answer is to record the inability explicitly and leave agy profile integration to whichever plan owns it. If the maintainer wants agy parity, that is a scope decision for them, not a silent expansion here.

### OQ-03: Is the field name and unit contract this plan sets binding on the `runanalytics` Set, and who reconciles if that Set lands first?

- Blocking: no
- Status: open
- Owner: this plan's executor for the reading, the maintainer for the coordination
- Resolution or deferral rationale: NOT blocking, because E-06 requires those plans' statuses be READ at execution time and the CONSUME-rather-than-duplicate rule applies whichever landed first, so the plan is executable in either order. It is recorded because two artifacts naming one fact is the specific waste this note exists to prevent: `5f2h8i`, `aflsz3` and `8hald1` all reference model and price data, none of them can produce it today, and none declares a field name. Whoever executes second must bind to the first's name rather than adding a sibling field. If both are in flight simultaneously, that is a maintainer sequencing call.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the resolved model as it appears in a real `state.json` for a run where no `--model` was passed, showing an actual model id rather than `host-default`. Paste the unchanged `model` field beside it, proving the true statement about the flag was preserved. Paste the new provenance value and its admission to `PROVENANCE_VALUES`. Paste proof the host config was read only through `oc_models`' readers (show the call, not a similar function). Paste `aw sanitize --agent` before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the recorded card from a real `state.json`, showing all four components, the model it applies to, the digest, and the launch-time-snapshot label. State the UNIT explicitly and paste the code that enforces it. Paste a card with `cache_read` ABSENT beside one with `cache_read` genuinely zero, showing they are DISTINGUISHABLE in the record; that contrast is the `x0spmh` trap and a V-02 without it is incomplete. State where the card's digest lives and why it is or is not the profile's `config_digest`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a run's reported cost, then EDIT the host config's prices, then paste the same run's reported cost again, showing it UNCHANGED. Paste a pre-change run (no recorded card) showing its card reported as ABSENT rather than borrowed. Paste proof no second cost computation was added (a grep for a tokens-times-price expression in the changed files, returning only what already existed).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: state the agy decision and paste the code implementing it. Paste an agy run record (synthetic, and LABELLED synthetic) showing either a recorded card or an explicit cannot-resolve marker distinguishable from an oc unresolvable. Paste the AST-measured oc-to-agy import count before and after, showing it did not increase from 47. Paste the grep confirming agy's profile integration status at execution time, since it may have changed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the tests and their actual runner output for EVERY unknown path: no config, `.jsonc` config, config with no cost block, card missing `cache_read`, and a card value that is a string or negative. For each, paste the recorded value showing it is distinguishable from a resolved card AND from zero. Paste the historical card-less fixture's result. Paste proof no test reads `.aw/records/runs/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `- Status:` line and directory of `5f2h8i`, `aflsz3` and `8hald1`, read at validation time. State which branch applied and what was done. Paste the field NAME and UNIT as the stated contract. Paste proof this plan implemented NO effective-dated schedule, NO pooled-aggregate exclusion, NO per-model comparison and NO cost recomputation: name each and show the absence, since the whole point of this V-item is that the boundary held.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the seven paths in `- Scope-Paths:`. Do NOT rebuild `launch_profile_record`; extend it. Do NOT write a second host-config reader. Do NOT change `oc_models.sync_provider`, its write path, its atomic write, or its backups. Do NOT implement an effective-dated price schedule, a pooled-aggregate exclusion rule, a per-model comparison, or a cost recomputation: all four are `runanalytics` deliverables. Do NOT touch `run_viewer.py` or any `aw runs` view. Do NOT back-fill a card onto a historical run. Do NOT add a symbol to `oc_runipd` for `agy_runipd` to import. Do NOT edit spec `25kzda` unless the spec-sync reading requires it, and never its §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` and `agy_runipd.py` are the highest-contention files in this repository and are being edited by live runs; measured, their line numbers moved roughly 70 and 95 lines in a single day, and the backlog item's own citations were already stale. Find `launch_profile_record`, `resolve_launch_profile`, `runner_profiles.resolve`, `PROVENANCE_VALUES`, `oc_models.resolve_config_path`, `models_from_config`, and `per_million` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved w33lrl --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `vlf75p`, which this plan carries as `- From-Backlog:` and whose `- Blocks-Release: next` gate it inherits. The item's already-shipped and `runanalytics`-owned portions are recorded in the item itself with their owners named, so closing it does not silently drop them.
