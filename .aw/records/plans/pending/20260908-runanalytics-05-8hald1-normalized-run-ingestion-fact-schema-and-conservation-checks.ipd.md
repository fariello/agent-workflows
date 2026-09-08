# IPD: Normalized run ingestion, fact schema, and conservation checks

- Date: 2026-09-08
- Kind: child
- Concern: Convert heterogeneous historical and current runner artifacts into one complete, auditable, privacy-safe analytical fact model.
- Scope: Inventory sources, implement OpenCode/Agy/version-tolerant adapters, define normalized facts and provenance, enforce metric conservation, and populate the Order-02 cache.
- Scope-Paths: agent_workflows/run_analytics.py, agent_workflows/run_analytics_schema.py, agent_workflows/run_analytics_sources.py, tests/test_run_analytics.py, tests/test_run_analytics_sources.py
- Item-Dependencies: executed:5f2h8i, executed:bzz5e6
- Status: approved
- Readiness: go-pending-approval
- Set: runanalytics
- Order: 5
- Highest E allocated: 08
- Author: Codex
- Id: 8hald1
- Approval: 2026-09-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-08 approved (aw set): status set to approved

- 2026-09-08 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-063..PR-072, ALL TEN FIXED, no open findings. The verdict token is stated explicitly because `plan_readiness.newest_verdict` reads the newest review record's first verdict token and falls back to a negative scan when none is present. THE ROOT FINDING IS THAT THE PLAN BELIEVED IT HAD NO DATA TO TEST AGAINST, AND THAT BELIEF HID TWO REAL DEFECTS (PR-063, F-1). The conventions asserted "the checkout contains no live run corpus"; measured, 135 run directories exist, ALL carrying `state.json`, `events.jsonl`, `execution-report.md`, `sessions/`, `outcomes/` and `prompts/`, across THREE driver generations (`oc_runipd.py` 120, `runipd.py` 13, `ipdrunner.py` 2) with ZERO Agy. Order 01's review corrected the identical false claim, so it is a Set-wide authoring error. Measuring that corpus then falsified two of this plan's core assumptions. FIRST AND MOST IMPORTANT (PR-064, F-2): THE STATED CONSERVATION EQUATION FAILS ON REAL DATA. `input + output + cache == total` holds for 174 of 176 real attempts and FAILS for 2, both carrying a `reasoning` key, where the shortfall equals `reasoning` EXACTLY (deltas 2658 and 1120); reformulated as `sum(every key except total) == total` it holds 176 of 176. So the authored form would have fired a FALSE conservation violation on real runs, and the natural reaction is to loosen the assertion, which destroys the only mechanism this plan has for making double counting detectable. E-06 now implements the all-components form and V-06 requires BOTH forms pasted so the choice is evidenced rather than asserted. SECOND (PR-065, F-3): THE TOKEN VOCABULARY WAS WRONG IN BOTH DIRECTIONS, naming a cache read/write split that appears nowhere in the corpus while omitting `reasoning`, which appears; E-05 now stores an OPEN component map so an unseen sixth key survives. THIRD (PR-066, F-4), the privacy requirement was correct but untethered: measured, ALL 135 `state.json` files carry an absolute `repo` path and scanning that single field returns `home-path` and `handle` BOTH at `fail`, while the corpus holds 472 prompt and 460 session files (~238 MB of conversation), so E-08 now requires the read-side proof be run over facts built from the REAL corpus with a control run, and requires consuming Order 02's projector rather than writing a second one. ALSO FIXED: two promised sources exist in ZERO real runs (`ledger.jsonl` and `telemetry/`), so both are fixture-only and the plan implied coverage the corpus cannot supply (PR-067, F-5); `schema_version` is uniformly `1` and cannot discriminate the three generations, while the REAL drift surface is a stable 14-key core plus exactly four varying keys across six key shapes (PR-068, F-6); the three E-items were mechanically sized, as E-03 alone named five deliverables, now EIGHT items with V-01..V-08 to bijection and `Highest E allocated` 03 -> 08, the fourth sibling split after `bzz5e6` 3->6, `lhccjf` 3->8 and `5f2h8i` 3->7 (PR-069, F-7); the gate carried no execution contract, fifth sibling in a row (PR-070, F-8); the corpus parses 100 percent clean (1428 of 1428 event lines) so the required corrupt-line case has no real exemplar and must be fixture-driven (PR-071, F-9); and no baseline was recorded, now `2 failed, 5655 passed` with both failures attributed as pre-existing live-corpus couplings, plus 16 escaped backticks unescaped after Order 01's six, Order 02's four, Order 03's ten and Order 04's eighteen (PR-072, F-10). Two decisions hidden behind "No open questions" plus one settled by measurement are now OQ-01..OQ-03. WHAT THE PLAN GOT RIGHT AND KEEPS: the insistence on storing raw numeric observations rather than chart aggregates, the refusal to force overlapping activities to sum to elapsed wall time (publishing `observed_activity_time`/`unattributed_time`/`overlap_time` instead), the labelling of derived totals, and the gate's rule that missing, unavailable and not-applicable are distinct and none of them is zero.

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): specified source precedence, normalized grains, provenance, conservation, partial-run handling, and quality reporting.

## Goal

Create the stable data layer used by every chart, query, export, and finding. It must preserve unsummarized numeric timing and usage facts, distinguish measured/recorded/derived/missing values, tolerate historical schema drift, and make double counting detectable.

BUILD IT AGAINST THE REAL CORPUS, WHICH EXISTS. The authored conventions claimed the checkout has no live run corpus; it has 135 runs spanning three driver generations (F-1). That correction is not cosmetic, because measuring them falsified two of this plan's core assumptions: the four-term token conservation equation FAILS on real data where an all-components sum holds (F-2), and the token vocabulary contains `reasoning` while containing no cache read/write split (F-3). Treat the corpus as a read-only smoke corpus, keep checked-in fixtures authoritative, and never commit any of it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

RIGHT-SIZING NOTE. Authored with THREE E-items, as were eight of the Set's eleven plans; the count-based lint conforms and cannot see conceptual density. E-03-as-authored named FIVE independent deliverables (precedence, deduplication, conservation, partial-run semantics, quality summaries, cache integration) across unrelated test surfaces, and E-02 named ten fact grains in one item. Siblings `bzz5e6` (3 -> 6), `lhccjf` (3 -> 8) and `5f2h8i` (3 -> 7) were split for the identical reason. Split into eight items across four groups.

### Task group 1: Sources

- [ ] E-01 Build the versioned source INVENTORY against the real corpus, and record what each generation actually provides.
  MEASURED AT REVIEW, SO THE ADAPTER MATRIX IS NOT GUESSWORK. The checkout holds 135 run directories (the "no live run corpus" claim was FALSE; see F-1). All 135 carry `state.json`, `events.jsonl`, `execution-report.md`, `sessions/`, `outcomes/` and `prompts/`. THREE driver generations are present: `oc_runipd.py` (120), `runipd.py` (13) and `ipdrunner.py` (2), and there are ZERO Agy runs, so the Agy adapter cannot be validated against real data and must be fixture-only with that limit stated. `schema_version` is uniformly `1` across all 135, so it does NOT discriminate generations: infer the generation from the `driver.path` basename, and treat `schema_version` as necessary but insufficient.
  TWO ARTIFACTS THE PLAN ASSUMES EXIST DO NOT EXIST ANYWHERE IN THE CORPUS: `ledger.jsonl` is present in ZERO of 135 runs, and `telemetry/` in ZERO (the latter is expected, since Order 04 has not executed). So the "ledger distinctions" this item promises to recognize are unexercisable against real data, and every telemetry-present case is fixture-only. Say so rather than implying coverage.
  - Depends on: none
  - Expected outcome: an inventory keyed on the `driver.path` basename with the measured per-generation artifact matrix; an explicit record of which sources are fixture-only (Agy, ledger, telemetry) and why; source coverage and warnings recorded without reading prompt or response content.
  - Execution state: pending

- [ ] E-02 Implement the SCHEMA-DRIFT tolerance against the measured variance, not against an imagined one.
  MEASURED: `state.json` has SIX distinct top-level key shapes across the corpus. Fourteen keys are present in ALL of them (`created_at`, `driver`, `manifest`, `manifest_sha256`, `options`, `queue`, `repo`, `runbook`, `runbook_sha256`, `run_id`, `schema_version`, `selectors`, `set_sessions`, `updated_at`), and FOUR vary (`_invocation_start_mono`, `run_order`, `session_id`, `session_turn_counts`). That is the real drift surface: a stable core plus four optional keys. Treat every varying key as optional-by-contract, and treat an unknown key as recorded-and-ignored rather than fatal, since a newer driver will add more.
  - Depends on: E-01
  - Expected outcome: the fourteen-key core required, the four measured optional keys tolerated when absent, an unknown key recorded in the coverage report and never fatal; a test per key shape.
  - Execution state: pending

- [ ] E-03 Implement the source PRECEDENCE by extracting or reusing the existing authority rather than restating it.
  `run_viewer.extract_step_usage` (`:639`) already implements the exact precedence this plan wants: it prefers a stored `attempt["cost"]`/`attempt["tokens"]` and falls back to `extract_log_metrics` over the session log only when both are absent (`:665-684`), including the path-resolution fallbacks for a relative or moved log. That behavior is tested. Extract it into a shared authority or call it; do NOT write a second precedence rule, because two rules that agree today will disagree after one bug fix.
  - Depends on: E-01
  - Expected outcome: ONE precedence implementation shared by the viewer and the ingester, with a test proving both produce identical results on the same fixture; no second fallback rule.
  - Execution state: pending

### Task group 2: Facts

- [ ] E-04 Define the normalized FACT SCHEMA and its provenance vocabulary: stable ids, source provenance, runner/model/variant, timestamps or duration, run/set/IPD/attempt/phase keys, and the measured/recorded/derived/missing distinction.
  KEEP THE FOUR-STATE DISTINCTION IRREDUCIBLE, since the gate depends on it: `missing`, `unavailable` and `not-applicable` are different facts and none of them is zero. Encode them as distinct values, never as a nullable number, because a nullable number invites a later `or 0`.
  - Depends on: E-02, E-03
  - Expected outcome: typed fact records that round-trip; the four-state provenance encoded as an explicit vocabulary; phase separation (review, execute, verify, recovery) representable; a test that a missing value cannot be silently read as zero.
  - Execution state: pending

- [ ] E-05 Populate the USAGE and TIME facts, preserving the raw component observations rather than only aggregates.
  THE TOKEN KEY VOCABULARY IS MEASURED AND IS NOT THE FOUR THE PLAN NAMES. Across 176 attempts carrying usage, the keys observed are `input` (176), `output` (176), `cache` (176), `total` (176) and `reasoning` (2). The plan's Findings section enumerates "input, output, cache read/write when distinguishable, and total" and never mentions `reasoning`; there is no separate cache-read/cache-write split anywhere in the corpus, only a single `cache`. So the schema must carry an OPEN component map, not five named columns, or the next provider key is silently dropped.
  - Depends on: E-04
  - Expected outcome: usage stored as an open component map plus a total, with the measured five keys covered and an unseen sixth key preserved rather than discarded; wall-clock and activity intervals stored separately, publishing `observed_activity_time`, `unattributed_time` and `overlap_time` without forcing overlapping activities to sum to elapsed time.
  - Execution state: pending

### Task group 3: Integrity

- [ ] E-06 Implement the CONSERVATION check as a sum over ALL component keys, which is the form that actually holds.
  THIS IS THE MOST IMPORTANT CORRECTION IN THIS REVIEW, AND IT IS MEASURED. The plan's stated equation reconciles "input/output/cache/total tokens". Tested against all 176 real attempts: `input + output + cache == total` holds for 174 and FAILS for 2, both on run items where a `reasoning` key is present, and in both cases the shortfall equals `reasoning` EXACTLY (deltas 2658 and 1120). Reformulated as `sum(every key except total) == total`, it holds for 176 of 176 with ZERO mismatches. So the four-term equation would have shipped a conservation check that fires a false violation on real data, and an executor would then likely have "fixed" it by loosening the assertion, which destroys the whole point of the check. Implement the all-components form, and make an unknown component key participate in the sum automatically.
  - Depends on: E-05
  - Expected outcome: conservation expressed as total-versus-sum-of-all-components; the two `reasoning` attempts pass; a synthetic attempt with an invented component key also passes without a code change; a genuine mismatch still fails.
  - Execution state: pending

- [ ] E-07 Implement DEDUPLICATION, partial-run semantics and the data-quality summary, so an incomplete or damaged run degrades only itself.
  Overlaps and unknown gaps must be explicit rather than smoothed. One malformed artifact degrades ITS run and no other. Note the corpus is CLEAN on this axis today: all 1428 event lines across 135 runs parse, so corrupt-line handling has no real-data exemplar and must be driven by a deliberately corrupted fixture.
  - Depends on: E-06
  - Expected outcome: a resumed or multi-attempt run is not double counted; a corrupted fixture line is skipped with a recorded warning and does not abort the run or affect other runs; the quality summary names what was missing, unavailable or not-applicable per run.
  - Execution state: pending

### Task group 4: Privacy and handoff

- [ ] E-08 Route every persisted fact through Order 02's EXISTING privacy projector and prove the boundary held with the shipped detector.
  DO NOT WRITE A SECOND SANITIZER OR A SECOND PROJECTOR. Order 02 (`bzz5e6`) E-04 owns "the single allowlist-based privacy PROJECTOR that every persisted fact crosses" and its expected outcome is that the projector is "the only path by which a fact reaches the envelope". This plan is a producer of facts, so it consumes that projector; a parallel one here would defeat the property Order 02 exists to establish.
  THE PRIVACY RISK HERE IS CONCRETE AND MEASURED, NOT THEORETICAL. Every one of the 135 `state.json` files carries an ABSOLUTE `repo` path, and scanning just that one field with the shipped detector returns `home-path` and `handle`, BOTH at `fail` severity. The corpus also holds 472 prompt files and 460 session files totalling roughly 238 MB of model conversation. So the source data genuinely contains what must never reach a fact, and the read-side check must be run against output built from the REAL corpus, not only from sanitized fixtures.
  - Depends on: E-07
  - Expected outcome: facts reach the cache only through Order 02's projector; `leak_sanitizer` reports clean over facts built from the real corpus AND a control run proves the same invocation flags the raw `repo` field; no prompt, response, file-content or absolute path is retained.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `run_viewer.extract_step_usage` (`:639`) already prefers stored attempt totals and falls back to session-log extraction. VERIFIED AT REVIEW: it reads `attempt["cost"]`/`attempt["tokens"]` first and only calls `extract_log_metrics` when both are absent (`:665-684`), including path fallbacks for a relative or moved log. Reuse it or extract a shared authority; a second precedence rule will diverge from this one after the first bug fix.
- Driver `events.jsonl` and the hash-chained `ledger.jsonl` are different formats and authorities. MEASURED, AND THIS CHANGES THE WORK: `ledger.jsonl` is present in ZERO of the 135 real runs, so the ledger adapter has no real-data exemplar and is fixture-only. Do not imply coverage the corpus cannot provide.
- Existing run summaries separate execute and verify usage; the normalized schema must retain that split and add review/recovery when present.
- CORRECTED AT REVIEW: THE CHECKOUT DOES CONTAIN A LIVE RUN CORPUS, and the authored claim that it does not was false. Measured: 135 run directories, ALL carrying `state.json`, `events.jsonl`, `execution-report.md`, `sessions/`, `outcomes/` and `prompts/`. Three driver generations (`oc_runipd.py` 120, `runipd.py` 13, `ipdrunner.py` 2) and ZERO Agy runs. Order 01's review found and corrected the identical false claim in its own plan, so this is a Set-wide authoring error, not a one-off. USE THE CORPUS as a read-only smoke corpus and as the source of the measured facts below; keep checked-in synthetic fixtures AUTHORITATIVE for assertions, since the corpus is gitignored, box-local, mutable and grows with every run. Never commit any part of it.
- `schema_version` is uniformly `1` across all 135 runs, so it does NOT discriminate driver generations. Infer the generation from the `driver.path` basename and treat `schema_version` as necessary but insufficient.
- THE REAL DRIFT SURFACE IS A STABLE CORE PLUS FOUR OPTIONAL KEYS. Measured: six distinct `state.json` top-level key shapes; fourteen keys present in every shape; exactly four vary (`_invocation_start_mono`, `run_order`, `session_id`, `session_turn_counts`).
- Source run directories are read-only. The only writes are privacy-safe cache entries in the reserved analytics subtree, whose path is resolved through Order 01's (`xbwq8n`) resolver and never composed by hand: `runner_shared.state_root:188-189` hardcodes the repository case while the records root is relocatable by `records_backend` (`project_context.py:783-790`), and Order 01 exists to remove that literal from its six live sites.
- ORDER 02 OWNS THE PRIVACY PROJECTOR AND THIS PLAN CONSUMES IT. `bzz5e6` E-04 is "the single allowlist-based privacy PROJECTOR that every persisted fact crosses", whose stated outcome is that it is "the only path by which a fact reaches the envelope". Writing a second projector or a second sanitizer here would defeat exactly the property Order 02 exists to establish. `leak_sanitizer` remains the independent READ-side oracle.
- THE PRIVACY HAZARD IN THIS SOURCE DATA IS MEASURED, NOT HYPOTHETICAL: every one of the 135 `state.json` files carries an ABSOLUTE `repo` path, and scanning that single field with the shipped detector returns `home-path` and `handle`, both at `fail`. The corpus also holds 472 prompt files and 460 session files, roughly 238 MB of model conversation, which is precisely the content that must never enter a fact.

## Findings

Required fact grains are intentionally fine enough to compute global medians, dispersion, robust quantiles, regressions or ANOVA later without reparsing source files. Store raw numeric observations and categorical keys, not only chart aggregates.

For time attribution, represent wall-clock intervals and activity intervals separately. Do not force overlapping activities to sum to elapsed wall time. Publish `observed_activity_time`, `unattributed_time`, and `overlap_time` so totals remain honest.

For token totals, retain every provider-reported component and the total. CORRECTED AT REVIEW: the authored wording named "input, output, cache read/write when distinguishable, and total", which does not match the data. Measured over 176 real attempts, the keys are `input`, `output`, `cache` and `total` (176 each) plus `reasoning` (2); there is NO cache-read/cache-write split anywhere in the corpus, and `reasoning` was unanticipated. Store an OPEN component map so an unseen sixth key is preserved rather than dropped. A derived total must be labeled; never silently assume cache is additive when a provider already includes it.

### Findings (review, measured 2026-09-08 at HEAD `0aea0771`)

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | plan conventions as authored; `.aw/records/runs/` | **"THE CHECKOUT CONTAINS NO LIVE RUN CORPUS" IS FALSE, AND IT IS THE CLAIM THIS PLAN LEANS ON MOST.** 135 run directories exist, all with `state.json`, `events.jsonl`, `execution-report.md`, `sessions/`, `outcomes/` and `prompts/`. Three driver generations (`oc_runipd.py` 120, `runipd.py` 13, `ipdrunner.py` 2) and ZERO Agy. An ingestion plan that believes it has no real data to test against will validate its adapters only against fixtures it wrote from its own assumptions, which is how a parser ships that has never met the format. Order 01's review corrected the identical false claim, so it is a Set-wide authoring error | enumerated and parsed all 135 `state.json` files |
| F-2 | HIGH | plan E-03's conservation equation; 176 real attempts | **THE STATED CONSERVATION EQUATION FAILS ON REAL DATA.** "input/output/cache/total tokens ... reconcile" holds for 174 of 176 attempts and FAILS for 2, both carrying a `reasoning` key, where the shortfall equals `reasoning` EXACTLY (deltas 2658 and 1120). Reformulated as `sum(every key except total) == total` it holds 176 of 176. So the authored form would have fired a FALSE conservation violation on real runs, and the likely reaction is to loosen the assertion, which destroys the check's entire value | computed both forms over every attempt in the corpus; the two failing runs and their exact deltas identified |
| F-3 | HIGH | plan Findings' token vocabulary; measured key counts | **THE TOKEN KEY VOCABULARY IS WRONG IN BOTH DIRECTIONS.** The plan names a cache read/write split that appears NOWHERE in the corpus (only a single `cache` key), and omits `reasoning`, which does appear. A schema built from the authored list would have five named columns, silently dropping `reasoning` and any future component key. The fix is an OPEN component map | key frequency over 176 attempts: `input`/`output`/`cache`/`total` 176 each, `reasoning` 2 |
| F-4 | HIGH | `.aw/records/runs/*/state.json` `repo` field; `leak_sanitizer.scan_text` | **THE SOURCE DATA CONTAINS EXACTLY WHAT MUST NEVER REACH A FACT, MEASURED.** All 135 `state.json` files carry an ABSOLUTE `repo` path; scanning that one field returns `home-path` and `handle`, BOTH at `fail`. The corpus also holds 472 prompt files and 460 session files, roughly 238 MB of conversation. The plan's privacy requirement was correct but untethered: it never established that the risk is live, so the read-side check could have been run only over sanitized fixtures and proven nothing | `scan_text` over the `repo` field of a real `state.json`; prompt/session file counts and byte total |
| F-5 | MEDIUM | plan E-01's promised sources; corpus | **TWO PROMISED SOURCES DO NOT EXIST IN ANY REAL RUN.** `ledger.jsonl` is present in ZERO of 135 runs and `telemetry/` in ZERO (the latter expected, since Order 04 has not executed). The item promised to "recognize ... telemetry, and ledger distinctions", implying coverage the corpus cannot supply; both are fixture-only and the plan must say so rather than let a reviewer read validated support into it | presence counts across all 135 runs |
| F-6 | MEDIUM | corpus; plan's version-tolerance requirement | `schema_version` is uniformly `1` across all 135 runs, so it cannot discriminate the three driver generations; the generation is only inferable from the `driver.path` basename. Separately, the REAL drift surface is a stable 14-key core plus exactly four varying keys (`_invocation_start_mono`, `run_order`, `session_id`, `session_turn_counts`) across six distinct key shapes. "Version-tolerant" was a requirement without a measured target | parsed `schema_version` and computed the key-shape lattice across the corpus |
| F-7 | MEDIUM | plan E-01..E-03; eight of eleven Set plans at exactly 3 E-items | **THE E-ITEMS WERE MECHANICALLY SIZED.** E-03 named five independent deliverables (precedence, dedup, conservation, partial-run semantics, quality, cache integration) across unrelated test surfaces; E-02 named ten fact grains in one item. The count-based lint conformed before and after the split, so it cleared nothing. Fourth sibling with this finding (`bzz5e6` 3->6, `lhccjf` 3->8, `5f2h8i` 3->7) | `grep -c` across the Set; lint conforming both ways |
| F-8 | MEDIUM | plan gate as authored | The gate carried two sentences and NO execution contract: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle move, no re-locate-by-symbol warning. Fifth sibling in a row, so it is a property of the authoring pipeline | plan read; four sibling review records read |
| F-9 | LOW | corpus event lines | The corpus is CLEAN on the corruption axis: all 1428 event lines across 135 runs parse. So the plan's required "corrupt event line" case has no real-data exemplar and must be driven by a deliberately corrupted fixture. Worth stating so an executor does not conclude the handling is exercised by the smoke corpus | parsed every line of all 135 `events.jsonl` files |
| F-10 | LOW | suite baseline; plan source (16 escaped backticks pre-fix) | No baseline was recorded despite requiring a bare suite run. Measured bare at `0aea0771`: `2 failed, 5655 passed, 3 skipped, 2 xfailed`, both failures (`test_orchestrator_retirement::RealRepositorySets`, `test_plan_readiness::ApprovalGateRealCorpusTests`) pinned to the live mutable plan corpus and pre-existing. Also 16 escaped backtick pairs rendered as literal backslashes, after Order 01's six, Order 02's four, Order 03's ten and Order 04's eighteen | bare run at review; `grep -c` before the fix |

## Proposed changes (ordered, validatable)

1. E-01 inventories the sources against the REAL corpus and names which adapters are fixture-only.
2. E-02 tolerates the measured drift (a 14-key core plus four optional keys); E-03 reuses the ONE existing precedence authority rather than restating it.
3. E-04 defines the fact schema and the irreducible four-state provenance; E-05 stores usage as an OPEN component map and keeps wall-clock and activity time separate.
4. E-06 implements conservation in the all-components form, the only form that holds on real data.
5. E-07 adds deduplication, partial-run semantics and the quality summary so damage stays local.
6. E-08 routes every fact through Order 02's existing projector and proves the boundary with the shipped detector against real-corpus output.

## Deferred / out of scope (with reason)

- Activity classification rules and statistical analysis are Order 06 (`aflsz3`, taxonomy/pricing/statistics/findings). Verified against its front matter.
- HTML rendering and query UX are Orders 07 (`6eq3oq`, offline SPA and report bundle) and 08 (`mm5p3v`, `aw runs analyze` and query). Verified against their front matter.
- The privacy projector and the cache envelope are Order 02 (`bzz5e6`); the run-root resolver and the reserved `analytics/` namespace are Order 01 (`xbwq8n`); the telemetry this plan ingests is produced by Orders 03 (`lhccjf`) and 04 (`5f2h8i`). This plan consumes all four and reimplements none of them.
- Parsing natural-language conversations to infer activity is excluded; only structured events, tool metadata, file categories, and bounded non-content signals may be used.
- Uploading raw or normalized facts is Order 09.

## Scope check

- Over-scope: no taxonomy policy, price tables, statistics, UI, CLI leaf, or transport. Specifically, and each for a measured reason: do NOT write a second privacy projector or a second sanitizer (Order 02's `bzz5e6` E-04 is the single projector every persisted fact must cross, and `local_leaks` is deliberately a thin re-export of one engine); do NOT write a second usage-precedence rule (`run_viewer.extract_step_usage:639` is the tested authority to reuse or extract); do NOT add a new `.aw/records/runs` literal (Order 01 owns the resolver and the literal already exists at six sites); do NOT write into any source run directory, which is read-only; do NOT weaken `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS`; do NOT commit any part of the live run corpus, which is gitignored and contains absolute paths that the leak detector flags at `fail`; and do NOT edit a spec, since none is declared in `Scope-Paths`.
- An out-of-scope edit is not forbidden outright, it must be JUSTIFIED: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path.
- Under-scope: includes every required fact grain, source compatibility, phase separation, provenance, quality, partial runs, deduplication, and cache handoff. The all-components conservation form (E-06), the open token component map (E-05), the measured drift target (E-02) and the real-corpus privacy proof (E-08) were under-scope before review.

## Required tests / validation

Baseline, measured bare at HEAD `0aea0771`: `2 failed, 5655 passed, 3 skipped, 2 xfailed`. Both failures (`tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` and `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`) are pinned to the live mutable plan corpus and are PRE-EXISTING. Re-measure in the executing worktree and compare failing NODE IDS; the criterion is an empty delta against your own baseline, never a total.

FIXTURES ARE AUTHORITATIVE; THE LIVE CORPUS IS A READ-ONLY SMOKE CHECK. Do not pin a test to `.aw/records/runs/`: it is gitignored, mutable, grows with every run, and carries absolute paths the leak detector flags at `fail`. Use it to confirm the fixtures resemble reality and to run the privacy proof against real-shaped input, then assert against fixtures. This is the same rule the sibling Orders adopted, and the two current suite failures are themselves live-corpus couplings, which is the argument made concrete.

- Fixtures for completed, failed, partial, cancelled, in-progress, resumed, multi-attempt, merge-failed, verifier-skipped, telemetry-present, telemetry-absent, OpenCode, Agy, old schema, corrupt event line, and missing artifact runs. NOTE WHICH OF THESE THE REAL CORPUS CANNOT EXERCISE, so their fixtures carry the whole weight: Agy (zero real runs), telemetry-present (zero), ledger (zero), and corrupt event line (all 1428 real lines parse).
- Exact conservation assertions for cost and tokens, in the ALL-COMPONENTS form (`sum(every key except total) == total`), not the four-term form, which is measured to fail on the two real attempts carrying `reasoning`. Include an attempt with an invented component key to prove the check is open rather than hardcoded, and an injected genuine mismatch to prove it can still fail.
- Per-attempt/per-IPD/per-run time; overlap and unattributed time, with a fixture whose activities deliberately overlap so the no-forced-sum property is exercised rather than asserted.
- Parser must not retain prompt, response, file-content, arbitrary command, raw host, or raw absolute-path canaries. Prove it BOTH ways: the projector refused them (write side, Order 02's) AND `leak_sanitizer` finds nothing in the output (read side), the latter run over facts built from the REAL corpus with a control run proving the same invocation flags a real `state.json`'s `repo` field. Do not commit a canary as a literal; generate it at test time or assemble it from fragments, as the detection engine does with its own patterns.
- Deterministic cache round-trip and source coverage report.
- Existing run viewer tests, focused analytics tests, bare `python3 -m pytest`, and `git diff --check`. Run the suite BARE; do not add `-n0`, a second `-q`, or `-p no:randomly`, since `pyproject.toml` `addopts` already supplies the intended flags.
- No test may parse the live corpus as its assertion source, spend real time, or reach the network.

## Spec / documentation sync

Schema and source-precedence documentation live beside the implementation. Order 10 (`9xycbh`) produces the user-facing data dictionary and compatibility matrix. This plan declares NO spec file in `Scope-Paths` and must edit none: the run-artifact contract is `25kzda` and Order 04 (`5f2h8i`) owns that amendment, so if execution concludes the contract must change, that is a STOP-and-raise rather than a unilateral edit.

"IF CORPUS EVIDENCE CONTRADICTS A SOURCE ASSUMPTION, UPDATE THIS IPD" WAS ALREADY TRUE AT REVIEW, AND THE CONTRADICTIONS ARE NOW RECORDED RATHER THAN LEFT FOR THE EXECUTOR TO DISCOVER. Four assumptions were contradicted by the real 135-run corpus: that no corpus exists (F-1), that the four-term conservation equation holds (F-2), that the token vocabulary has a cache read/write split and no `reasoning` key (F-3), and that ledger and telemetry sources are available to validate against (F-5). Those are in the Findings table with their measurements. RE-MEASURE at execution rather than trusting the numbers here: the corpus is mutable and grows with every run, so treat every count as a review-time snapshot and re-derive it.

## Open questions

"No open questions" was not accurate: the plan required two decisions it specified nowhere, and a third was settled by measurement at review. All are answerable from repository evidence rather than by asking, so each is recorded resolved with its basis. Every reviewed sibling in this Set carried the same inaccurate claim.

### OQ-01: What exactly must the conservation equation reconcile?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY MEASUREMENT, and this is the decision that most changes the code. The authored equation reconciles `input`, `output`, `cache` and `total`. Tested over all 176 real attempts it holds for 174 and FAILS for 2, both carrying a `reasoning` key, with the shortfall equal to `reasoning` exactly (2658 and 1120). The all-components form, `sum(every key except total) == total`, holds 176 of 176. So the equation is over ALL component keys, with an unknown key participating automatically. REJECTED: enumerating five named keys including `reasoning`, because that merely moves the failure to the next provider key nobody has seen; and loosening the assertion to a tolerance, because a conservation check that tolerates a mismatch detects no double counting, which is the one thing this plan exists to make detectable.

### OQ-02: Does this plan write its own privacy projector, or consume Order 02's?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW from the sibling's own text. Order 02 (`bzz5e6`) E-04 is "the single allowlist-based privacy PROJECTOR that every persisted fact crosses" and its expected outcome states it is "the only path by which a fact reaches the envelope". This plan is a fact PRODUCER, so it consumes that projector; a parallel one here would defeat the exact property Order 02 exists to establish, and `Item-Dependencies` already requires `executed:bzz5e6`. `leak_sanitizer` stays the independent READ-side oracle, with a control run required because a clean report and a detector that was not looking are indistinguishable. REJECTED: a local projector "just for facts", because two allowlists drift and the weaker one becomes the effective boundary.

### OQ-03: How is the real corpus used, given it exists after all?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW as "read-only smoke corpus, never authoritative, never committed". The 135 runs are genuine evidence about FORMATS and are the source of this review's measurements, so refusing to look at them would have shipped a parser validated only against its author's assumptions (F-1). But they are gitignored, box-local, mutable and growing, and they carry absolute paths the leak detector flags at `fail` (F-4), so they cannot be test fixtures: a test pinned to them would break as the corpus changes and would risk committing machine-identifying data. Checked-in synthetic fixtures remain authoritative for every assertion; the corpus is used to VERIFY the fixtures resemble reality and to run the privacy proof against real-shaped input. This mirrors Order 01's resolution of the same question.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the inventory's per-generation artifact matrix, re-measured in the executing worktree, showing the run count and the `driver.path` basename distribution (135 / 120 `oc_runipd.py` / 13 `runipd.py` / 2 `ipdrunner.py` at review; RE-MEASURE, the corpus grows with every run). Paste proof `schema_version` alone does not discriminate generations. State explicitly which adapters are FIXTURE-ONLY and why: Agy (zero real runs), `ledger.jsonl` (present in zero of 135) and `telemetry/` (zero, pending Order 04).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the measured set of distinct `state.json` top-level key shapes (six at review) with the required core and the optional keys named, and a test per shape. Paste behavior for an UNKNOWN top-level key showing it is recorded in the coverage report and is NOT fatal. Include a mutation check: make an unknown key fatal, show a test fails, revert.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the ONE shared precedence implementation and both call sites (the viewer and the ingester), plus a test asserting they return identical results on the same fixture. Paste proof no second fallback rule was added. Demonstrate the stored-total-beats-log-derived order and the log-path fallback for a relative or moved log.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a round-trip for every fact grain. Paste the four-state provenance vocabulary and a test proving `missing`, `unavailable` and `not-applicable` are distinct from each other AND from zero. Include a mutation check: coerce a missing value to zero, show a test fails, revert; that is the gate's own rule made falsifiable.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the observed token key vocabulary from the real corpus with counts (`input`/`output`/`cache`/`total` at 176 and `reasoning` at 2 when measured at review) and paste a fact built from an attempt carrying `reasoning`, showing it is preserved rather than dropped. Paste a synthetic attempt with an INVENTED component key showing it also survives, proving the map is open. Paste `observed_activity_time`, `unattributed_time` and `overlap_time` for a fixture with deliberately overlapping activities, showing they are not forced to sum to elapsed time.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the conservation result over the REAL corpus in the executing worktree, in BOTH forms: the four-term `input+output+cache == total` (expected to FAIL on the `reasoning` attempts, 174/176 at review) and the all-components `sum(all keys except total) == total` (expected 176/176). Naming the two runs and the exact deltas is what proves the implemented form is the correct one rather than the one that merely passes today. Then paste a genuine injected mismatch still FAILING, so the check is shown capable of firing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste a resumed and a multi-attempt fixture showing no double counting. Paste a deliberately corrupted event line being skipped with a recorded warning while its run still produces facts and OTHER runs are unaffected. State that the real corpus parses 100 percent clean (1428 of 1428 event lines at review), so this case is fixture-driven by necessity. Paste the quality summary distinguishing missing from unavailable from not-applicable.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste proof facts reach the cache ONLY through Order 02's projector (the call path, and a grep showing no second projector or sanitizer was added). Paste `aw sanitize --agent` over facts built from the REAL corpus reporting clean, AND a CONTROL run proving the same invocation flags the raw `repo` field of a real `state.json` (measured `home-path` and `handle`, both `fail`), since a clean report and a detector that was not looking are otherwise indistinguishable. Paste proof no prompt, response, file content or absolute path is retained. Do not commit a canary as a literal: generate it at test time or assemble it from fragments, as the detection engine does with its own patterns.
  - Observed evidence:
  - Result: pending

Additionally, and NOT as a separate V-item because it validates no single E-item: V-08 must also carry bare `python3 -m pytest` and `git diff --check` from the executing worktree, against the baseline the executor measured itself, comparing failing NODE IDS and never totals.

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: source precedence, schema grain, and conservation must be designed and tested as one data contract. NOTE THE SCOPE OF THAT ARGUMENT: it justifies ONE PLAN, not one ITEM. The three genuinely constrain each other, which is why they belong together; that does not make the inventory, the drift tolerance, the precedence reuse, the schema, the usage facts, the conservation check, the quality summary and the privacy handoff one deliverable, which is why the eight items exist (F-7).

EXECUTION CONTRACT. This plan requires explicit human approval (`aw ipd set approved 8hald1 --by-human --message ...`), and its `Item-Dependencies` refuse dispatch until BOTH `5f2h8i` (Order 04) and `bzz5e6` (Order 02) are `executed`. Both dependencies are load-bearing rather than bookkeeping: Order 02 owns the privacy projector every fact must cross and the cache this plan populates, and Order 04 produces the telemetry this plan ingests. Orders 06, 07, 08 and 10 consume what this plan defines, so the FACT SCHEMA is a contract, not an internal detail.

- Commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <path>`); never `git add -A`, never `-a`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index you never staged. Other agents and humans work concurrently in this checkout.
- NEVER COMMIT ANY PART OF THE LIVE RUN CORPUS. It is gitignored, and measured, its `state.json` files carry absolute paths that `aw sanitize` flags at `fail`. Run `aw sanitize --agent` before treating any output as shareable.
- THE HONESTY RULE, which outranks every convenience: when you report that tests passed, PASTE THE ACTUAL RUNNER OUTPUT. Never fill an `Observed evidence:` field from memory or from a matching execution checkmark. If a validation cannot be performed, say so plainly and leave it `pending`.
- RE-MEASURE EVERY CORPUS NUMBER IN THIS PLAN. The counts here (135 runs, 176 attempts, 1428 event lines, six key shapes, the two `reasoning` attempts) are a review-time snapshot of a tree that grows with every run. Re-derive them; do not cite them as current.
- RE-LOCATE EVERY CITED SYMBOL BY NAME, not by line number.
- Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

Never fill missing data with zero unless the source explicitly reports zero; missing, unavailable, and not-applicable are distinct. THREE STOP CONDITIONS: if the all-components conservation check fires on real data, INVESTIGATE the data rather than loosening the assertion, because a tolerant conservation check detects no double counting and this plan exists to make double counting detectable; if you find yourself writing a second privacy projector, a second sanitizer or a second usage-precedence rule, STOP, because each has exactly one owner already; and if a test needs the live corpus to pass, STOP and build a fixture, because the two current suite failures are precisely that mistake made earlier.
