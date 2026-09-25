# IPD: Make staged prompts a full artifact-organization and attention adopter

- Date: 2026-09-24
- Kind: child
- Concern: Graduates backlog `oxjt1d` (apply the artifact-organization model to `prompts/` reusing `artifact_core`) AND the first part of `mc5xts` (prompts as a Phase-3 attention adopter). MEASURED, the NAMING half of `oxjt1d` is ALREADY DONE: IPD `ubac5n` made staged prompts carry `<id6>` in the name and in the `<!-- aw-prompt: ... -->` comment, `check_engine._prompt_requires_id6` enforces it from cutover `20260921`, and spec `20260730-2152-01` Section 7 item 3 already reads "`prompts/`: DONE (`promptid6` `ubac5n`...)". What is NOT done is everything else the model promises: `aw index prompts` prints "WARN 'index' is not supported for prompts." (`artifact_types.TYPE_BACKENDS["prompts"]` has only `new`/`rename`/`group`); `check_engine.SUPPORTED["prompts"]` is `("names",)` with the comment "prompts / walkthroughs / roadmaps: no content validator today"; and `attention_contract.TREE_POLICY` still carries `TreePolicy("prompts", ".agents/prompts", False, "", "deferred to Phase 3 (OQ3)...")`, while `core.SCAN_ROOTS` lists no `.aw/records/prompts`, so `aw attention -t prompts --format json` reports `valid: true` with ZERO items over a 17-file corpus with 2 queued prompts in `pending/`.
- Scope: PROMPTS ONLY. IN: (a) attention adoption: flip the `prompts` TreePolicy to tracked, add a pure/total `_PROMPTS_MAP` over the prompt DISPOSITION enum, add the scan root, add a `_prompts_record` builder; (b) a generated, gitignored `INDEX.json`/`INDEX.md` manifest with `--check` via a new `prompts_index` module reusing `artifact_core`; (c) a prompts CONTENT validator so `aw check prompts` checks metadata, not just names; (d) reconcile the 2 live metadata/disposition mismatches; (e) amend the two specs whose text says prompts are deferred. OUT: comms and walkthroughs adoption, `mc5xts`'s persisted snapshot and plans `executing` state, prompt archive shards (see Deferred).
- Scope-Paths: agent_workflows/attention_contract.py, agent_workflows/attention.py, agent_workflows/artifact_core.py, agent_workflows/artifact_types.py, agent_workflows/check_engine.py, agent_workflows/prompts_index.py, agent_workflows/engine.py, .aw/.gitignore, .aw/records/prompts/README.md, .aw/records/prompts/executed/20260808-1948-01-attention-registry-spec-external-review.prompt.md, .aw/records/prompts/executed/20260828-2156-01-research-worktree-isolation-state-model.prompt.md, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md, tests/test_prompts_attention.py, tests/test_prompts_index.py, tests/test_attention_contract.py, tests/test_check_engine.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- Set: promptadopt
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: dx0u4s
- Approval: 2026-09-25, recorded via aw ipd set: status set to approved
- From-Backlog: oxjt1d

## Workflow history
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): Reviewed via /plan-review; 8 findings (PR-801..PR-808), all FIXED. REORDERED E-03..E-05: the authored order flipped the prompts TreePolicy to tracked BEFORE widening SCAN_ROOTS, which leaves the shipped TrackedTreeScanCoverageTests guard RED across three items (measured: no current scan root covers prompts); widening first is inert. Measured that only 1 of 17 prompts carries an id6, so an empty id is the norm the record builder and fixture must reflect. Measured that _prompt_requires_id6 is False for ALL 17 files, so two of E-07's three rules fire on zero live files and can only be evidenced on fixtures. Corrected the inverted 8/9 comment-coverage figure, replaced the nonexistent ScanRootClassificationInvariantTests citation, and measured the SCAN_ROOTS widening to add zero dangling citations. Rewrote the gate.

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog oxjt1d, mc5xts (first part only: prompts as attention adopters); re-measured that prompt naming/id6 is already done (`ubac5n`) while `aw index prompts` is unsupported, `aw check prompts` is names-only, and `aw attention -t prompts` yields 0 items because the tree is excluded and unscanned.

## Goal

Make `.aw/records/prompts/` a first-class adopter of the artifact-organization model beyond naming (manifest + content check) and a TRACKED attention tree, so the two queued prompts in `pending/` surface as `ready` in `aw attention` and `/whatnext` instead of being invisible.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline and failing tests first

- [x] E-01 RE-MEASURE the baseline before changing anything: `python3 -m agent_workflows index prompts` (expect "'index' is not supported for prompts"), `python3 -m agent_workflows attention -t prompts --format json` (expect `valid: true`, 0 items), `python3 -m agent_workflows attention --format json` (record `valid` and total item count), and the per-file disposition-vs-comment table. RE-DERIVE EVERY NUMBER; the figures below are LIVE-CORPUS counts that drift, so they are context and not the bar. Re-measured at review: 17 `.prompt.md` files (pending 2, executed 13, superseded 2, not-executed 0, reusable 0); NINE carry the leading `aw-prompt` comment and EIGHT do not (the authored plan had this pair inverted as "8 carry / 9 without"); of the nine, exactly TWO disagree with their bucket, both in `executed/` saying `Status: pending`, and they are the two files named in `- Scope-Paths:`; and exactly ONE prompt declares an `Id:` at all (`ng0ga4`). The whole-view total was `True 1508` at authoring and `True 1540` at review, which is the clearest illustration of why this item re-derives rather than asserts. Also record the dangling-citation baseline: `python3 -m agent_workflows index plans --check` and `python3 -m agent_workflows index research --check` output, because E-03 widens `SCAN_ROOTS`, whose module-level default those checks inherit (`artifact_core.find_dangling_citations`' `scan_roots` parameter defaults to `SCAN_ROOTS`, and `plans_index.check_drift` passes no override). Both already report findings at HEAD (plans: a stale-index line; research: `adopted-without-consumer` rows), so the bar is UNCHANGED-FROM-BASELINE, never "clean". STOP and report only if a STRUCTURAL claim moved (an index backend appeared, the tree became tracked, or the two mismatches were already fixed); a changed COUNT is expected and is recorded, not a stop.
  - Depends on: none
  - Expected outcome: pasted baseline outputs; every count stated as measured now, with any difference from the figures above noted rather than absorbed.
  - Execution state: performed

- [x] E-02 WRITE `tests/test_prompts_attention.py` BEFORE the implementation, over a temp fixture repo (`.aw/records/prompts/{pending,executed,superseded,not-executed,reusable}/` plus one `untracked/` file): assert `attention_contract.class_of("prompts", s)` for every disposition per the Findings table; assert `"prompts" in attention_contract.TRACKED_TREES`; assert `attention.scan(root)` yields one `prompts` item per bucketed prompt, a `pending/` prompt classed `ready`, and the `untracked/` file ABSENT; assert a prompt placed directly under `.aw/records/prompts/` (no bucket) yields `attention.missing-status`. THE ID FIXTURE MUST BE MOSTLY EMPTY, matching the live corpus: include at least one prompt WITH an `Id:` in its `aw-prompt` comment and at least two WITHOUT (one having a comment but no `Id:`, one having no comment at all), asserting an EMPTY id is a normal record rather than drift. That distribution is the measured reality (1 of 17 declares an id), so a fixture where every file carries one would test a corpus this repository does not have. ALSO add a README file to one bucket and assert it produces NO item, pinning the `is_nonartifact_name` filter that E-03's widened scan makes load-bearing. Run it and capture the FAILURES.
  - Depends on: E-01
  - Expected outcome: new test module exists and fails against unchanged code, with the failures being the `TRACKED_TREES` membership and `class_of` assertions (not a collection error).
  - Execution state: performed

### Task group 2: attention adoption (mc5xts part 1)

- [x] E-03 In `agent_workflows/artifact_core.py`, add `".aw/records/prompts"` and `".agents/prompts"` to `SCAN_ROOTS` with a comment citing this plan (the `releases` precedent, recorded in that constant's own comment: a tracked tree with no scan root is invisible while the view reports valid). DO THIS BEFORE FLIPPING THE POLICY, which is the reverse of the authored order, and the reason is a test that would otherwise fail across three items: `tests/test_attention_contract.py::TrackedTreeScanCoverageTests::test_every_tracked_tree_has_a_scan_root` asserts EVERY tree in `TRACKED_TREES` is covered by some entry of `SCAN_ROOTS`, and `prompts` is measurably NOT covered today (verified at review: no current root satisfies `_scan_root_covers_tree(r, "prompts")`). Flipping `tracked=True` first therefore leaves that guard RED for the whole E-04/E-05 window, so the executor could not tell its own new failures from the one it created and would be tempted to "fix" the guard. Widening the scan root first is inert while the policy is still `tracked=False`, because `attention.scan` skips an untracked policy before reading the file, so this ordering has no observable effect until E-04 lands. THE DANGLING RISK IS MEASURED AND SMALL: the widening adds 23 files to the 1592-file scan (17 prompts plus 6 READMEs) and produces ZERO new dangling citations for plans or research (driven at review with both cite matchers). If the executor's re-run of E-01's checks nonetheless shows NEW findings, fix only genuine broken citations in prompt files already declared in `- Scope-Paths:`, otherwise STOP and report the list.
  - Depends on: E-02
  - Expected outcome: `SCAN_ROOTS` contains both prompt roots; `python3 -m pytest -o addopts="" tests/test_attention_contract.py` still passes (26 tests at review), because an untracked tree with a scan root is the inert direction; `index plans --check` and `index research --check` output unchanged from E-01's capture.
  - Execution state: performed

- [x] E-04 In `agent_workflows/attention_contract.py`: change the `prompts` `TreePolicy` to `tracked=True`, owner `"aw prompts"`, reason naming the disposition-as-status contract; add `_PROMPTS_MAP` = `{pending: READY, executed: DONE, superseded: PARKED, not-executed: PARKED, reusable: PARKED}` per OQ-01 and register it in `CLASS_MAPS`; update the "v1 scope (OQ3)" comment above `TREE_POLICY` to say prompts are tracked (comms still deferred). Leave `docs-prompts` (the prompt LIBRARY) excluded. NOTE the `TreePolicy.root` stays `.agents/prompts`: `attention._classify_tree` rewrites `.aw/records/prompts` onto that policy already (verified at review, and it correctly does NOT collide with `.aw/records/prompt-library`, which remaps to `docs-prompts`), so changing the root would be a second, unmeasured change.
  - Depends on: E-03
  - Expected outcome: `class_of` is total over the prompt disposition enum; `docs-prompts` still excluded; `TrackedTreeScanCoverageTests` still GREEN, which is only true because E-03 landed first.
  - Execution state: performed

- [x] E-05 In `agent_workflows/attention.py`: add `_prompts_record(rel, path, text)` and dispatch it from `_record_for`. The NATIVE STATUS IS THE DISPOSITION DIRECTORY (first path component under `.aw/records/prompts/` or `.agents/prompts/`, alias `done` normalized to `executed`), mirroring `_plan_disposition_from_rel` — and reuse that function's SHARDING-SAFE derivation (the first component under the type dir, never `parent.name`, per its own comment about `<disposition>/YYYYMM/`) so a future `aw archive prompts` does not silently break this. The README states "its lifecycle is tracked by MOVING it between the buckets" (verified at review), and 8 of 17 files carry no in-file status at all, so the directory is the only total source. The id comes from `prompts.read_metadata_id6(text)`, which returns `None` for a file whose first line is not an `aw-prompt` comment; MEASURED AT REVIEW, that is the common case: exactly ONE of the 17 prompts declares an `Id:` at all (`ng0ga4`), so `_prompts_record` must treat an empty id as NORMAL and not as drift, and E-02's fixture must cover it. A file with no bucket emits `attention.missing-status`; an unknown bucket emits `attention.unknown-status`. Do NOT read the comment `Status:` here (that disagreement is `aw check prompts`'s job, E-07). READMEs need no special handling: `attention.scan` filters them via `attention_contract.is_nonartifact_name` before `_record_for` is reached (verified at review), which is why the widened scan's 6 README files do not become items.
  - Depends on: E-04
  - Expected outcome: `_record_for("prompts", ...)` returns an `Item` for every bucketed prompt, with an EMPTY id for the 16 that declare none, and `aw attention -t prompts` lists 17 items.
  - Execution state: performed

### Task group 3: manifest and content check (oxjt1d)

- [x] E-06 WRITE `tests/test_prompts_index.py` first (fixture repo as in E-02): `build_index_json` lists every bucketed prompt with `id6`/`set`/`order`/`disposition`/`kind`; `check_drift` reports `check.stale-index-missing` (info, exit 0) when absent, `check.stale-index-stale` when the on-disk JSON is edited, and `name-metadata-mismatch` when a clustered filename's id6 differs from the comment `Id:`. Capture failures (module absent). Then create `agent_workflows/prompts_index.py` modeled on `plans_index` (`scan_prompts`, `build_index_json`, `build_index_md`, `check_drift`, `run_index`), reusing `artifact_core.Drift`/`drift_exit_code`/`atomic_write` and `artifact_naming.parse_clustered`, stamping severity via `check_engine.enrich_drift` exactly as `plans_index.check_drift` does. Wire `"index": "prompts_index.run_index"` into `artifact_types.TYPE_BACKENDS["prompts"]`. Add `records/prompts/INDEX.json` and `records/prompts/INDEX.md` to `.aw/.gitignore` and to the anchored pattern tuple in `engine.py` beside the four existing `records/plans|research/INDEX.*` lines (the `ueg5cf` merge-conflict reason applies unchanged).
  - Depends on: E-05
  - Expected outcome: `aw index prompts` writes two gitignored files; `aw index prompts --check` clean after a rebuild.
  - Execution state: performed

- [x] E-07 Add a prompts content validator in `check_engine.check_content` and change `SUPPORTED["prompts"]` to `("names", "content")`. Rules (register each in `RULE_REGISTRY`): `check.prompt-metadata-missing` (error) for a prompt whose name requires id6 per `_prompt_requires_id6` but whose first line is not an `aw-prompt` comment; `check.prompt-id-mismatch` (error) when a comment `Id:` differs from the filename id6; `check.prompt-status-mismatch` (warning) when the comment `Status:` names a terminal disposition different from the bucket, or says `pending` inside a terminal bucket. STATE PLAINLY THAT THE FIRST TWO RULES FIRE ON ZERO LIVE FILES TODAY and say why, because the plan's original wording ("pre-cutover files are grandfathered, which covers all 9 comment-less files") implied the grandfathering is a narrow carve-out when it is in fact total: measured at review, `check_engine._prompt_requires_id6` returns False for ALL 17 prompts, because `PROMPT_ID6_CUTOVER_DATE` is `20260921` and every file's filename date precedes it (that constant's own comment says the value was chosen to sit strictly after the single conforming prompt so "that file's conformance stays incidental rather than load-bearing"). `check.prompt-id-mismatch` likewise cannot fire, since only one prompt declares an `Id:` and it matches its filename. So these two rules are FORWARD-LOOKING guards for prompts created after the cutover, and their only evidence can be SYNTHETIC-FIXTURE coverage, never live output; a plan claiming otherwise would be claiming enforcement it does not have. `check.prompt-status-mismatch` is the one rule with live subjects, and it has exactly two. Add the cases to `tests/test_prompts_index.py` (or a class in `tests/test_prompts_attention.py`), COVERING ALL THREE RULES ON FIXTURES including a post-cutover-dated filename with no comment, which is the only way the first rule is exercised at all. Update the `"content over prompts, a type with NO content validator"` row rationale in `tests/test_check_engine.py::EntryPointTests` (verified at review that its expected `()` still holds, because that shared tree contains a plan and a spec and no prompt; the prose must stop claiming no validator exists).
  - Depends on: E-06
  - Expected outcome: `aw check prompts` reports exactly the 2 live `check.prompt-status-mismatch` findings before E-08, and ZERO `check.prompt-metadata-missing` / `check.prompt-id-mismatch` findings, with the fixture tests proving those two rules fire when their conditions are actually met.
  - Execution state: performed

- [x] E-08 Reconcile the two live mismatches by editing ONLY the `Status:` field inside the leading `aw-prompt` comment of `20260808-1948-01-attention-registry-spec-external-review.prompt.md` and `20260828-2156-01-research-worktree-isolation-state-model.prompt.md` from `pending` to `executed` (their directory is the authority). Leave every prompt body byte-identical.
  - Depends on: E-07
  - Expected outcome: `aw check prompts` exits 0 with no `check.prompt-*` findings.
  - Execution state: performed

### Task group 4: spec and docs sync, full suite

- [x] E-09 Amend the specs and README: append a dated AMENDED note to spec `20260808-1945-01` beside OQ3 recording that prompts are now a tracked tree with the disposition map (comms still deferred to Phase 3); extend spec `20260730-2152-01` Section 7 item 3 to say the manifest and content check landed (plan `dx0u4s`), `comms/`/`walkthroughs/` still subsequent; add an "Index and attention" paragraph to `.aw/records/prompts/README.md` naming `aw index prompts [--check]`, `aw check prompts`, and the class mapping. Update `tests/test_attention_contract.py` so any assertion that prompts is excluded or unmapped reflects the new contract (the `class_of("prompts", "anything")` raise stays valid).
  - Depends on: E-08
  - Expected outcome: no spec or README text still says staged prompts are deferred or unindexed.
  - Execution state: performed

- [x] E-10 Run the bare suite `python3 -m pytest` with no extra flags, then `python3 -m agent_workflows attention --check` and `python3 -m agent_workflows check prompts`.
  - Depends on: E-09
  - Expected outcome: suite green; view valid; prompts check clean.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A prompt's metadata lives in ONE leading HTML comment, never a `- Id:` bullet (spec `20260808-1958-01-prompt-purity-lint` R1/P4, restated in `prompts.py` module docstring). So the attention record must read the id via `prompts.read_metadata_id6`, not `_plans_id`.
- Generated manifests are GITIGNORED, anchored per path, and a missing one is `info` (`plans_index.check_drift` comment "idxuntrack 02 (yvvf98)"; `.aw/.gitignore` "Written as four ANCHORED specific paths").
- `class_of` must be PURE and TOTAL over the native enum and the scanner may not infer state from prose (spec `20260808-1945-01` Section 6, quoted in the `reviews` TreePolicy comment).
- A TRACKED tree with no `SCAN_ROOTS` entry is INVISIBLE while `aw attention` still reports `valid: true`, and a shipped guard exists to stop exactly that (`tests/test_attention_contract.py::TrackedTreeScanCoverageTests`, added by `m867ox` after `releases` shipped in that state). The guard reads `TRACKED_TREES` against `SCAN_ROOTS`, so the two edits must land scan-root-first.
- `attention_contract.is_nonartifact_name` is what keeps README files out of the view; `attention.scan` applies it before `_record_for`, so a widened scan root does not require per-builder README handling.
- `.aw/records/prompts` and `.aw/records/prompt-library` are DIFFERENT trees and `attention._classify_tree` already separates them (`prompts` versus `docs-prompts`, verified by driving it). Do not "fix" the `prompts` `TreePolicy.root` spelling; the rewrite handles the `.aw/` twin.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). A TEST-CLASS name is a symbol and must exist: E-05 originally cited `ScanRootClassificationInvariantTests`, which is absent from this repository.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Naming/id6 adoption already done | `prompts.py` docstring "IPD `ubac5n`"; spec `20260730-2152-01` Section 7 item 3 "DONE" |
| F-2 | No index backend | `aw index prompts` -> "WARN 'index' is not supported for prompts." |
| F-3 | Names-only check | `check_engine.SUPPORTED["prompts"] = ("names",)` |
| F-4 | Tree excluded and unscanned | `TreePolicy("prompts", ".agents/prompts", False, ...)`; `.aw/records/prompts` absent from `artifact_core.SCAN_ROOTS`; attention `-t prompts` gives 0 items |
| F-5 | Disposition is the reliable status | CORRECTED AT REVIEW (the authored row had the pair inverted): 8 of 17 files have NO `aw-prompt` comment, 9 DO, and 2 of those 9 disagree with their bucket. Either way the conclusion stands and strengthens: the directory is the only source total over the corpus |
| F-6 | Existing lifecycle vocabulary | `lifecycle_style._PROMPTS_PAIRS`: pending READY, executed DONE, reusable REUSABLE, superseded SUPERSEDED, not-executed ABANDONED |
| F-7 | ADDED AT REVIEW: only ONE prompt carries an id6 | Driven `prompts.read_metadata_id6` over all 17 files: exactly one (`ng0ga4`) returns a value. So an EMPTY id is the norm, not the exception, which E-05's record builder and E-02's fixture must both reflect |
| F-8 | ADDED AT REVIEW: two of E-07's three rules have zero live subjects | `check_engine._prompt_requires_id6` returns False for ALL 17 prompts (driven), because `PROMPT_ID6_CUTOVER_DATE` is `20260921` and every filename date precedes it. So `check.prompt-metadata-missing` and `check.prompt-id-mismatch` can only ever be evidenced on synthetic fixtures; only `check.prompt-status-mismatch` has live subjects |
| F-9 | ADDED AT REVIEW: the tracked-tree scan-coverage guard forces the item order | `tests/test_attention_contract.py::TrackedTreeScanCoverageTests::test_every_tracked_tree_has_a_scan_root` asserts every `TRACKED_TREES` member is covered by a `SCAN_ROOTS` entry; measured, NO current root covers `prompts`. Flipping `tracked=True` before widening `SCAN_ROOTS` leaves that guard RED across three items, so this plan widens the root FIRST (the inert direction) |
| F-10 | ADDED AT REVIEW: the SCAN_ROOTS widening is measurably low-risk | Driven with both cite matchers: the widening adds 23 files to a 1592-file scan (17 prompts + 6 READMEs) and yields ZERO new dangling citations for plans or research. The 6 READMEs never become attention items, because `attention.scan` filters them through `attention_contract.is_nonartifact_name` before `_record_for` |

Proposed class mapping (disposition -> attention class): pending -> ready; executed (and alias done) -> done; superseded -> parked; not-executed -> parked; reusable -> parked (OQ-01).

## Proposed changes (ordered, validatable)

1. Baseline, re-derived (E-01), and failing attention tests (E-02).
2. Scan root FIRST (E-03, the inert direction), then the tracked policy + class map (E-04), then the record builder (E-05). This is the REVERSE of the authored order and it is deliberate: `TrackedTreeScanCoverageTests` fails on a tracked tree with no scan root, so flipping the policy first would leave that guard red across three items. A scan root on an untracked tree changes nothing observable, because the scanner skips an untracked policy before reading the file.
3. `prompts_index` manifest with `--check`, wired and gitignored (E-06).
4. Content validator and rules (E-07), with fixture coverage for the two rules that have no live subjects; fix the two live mismatches (E-08).
5. Spec/README/test sync (E-09); full suite and gates (E-10).

## Deferred / out of scope (with reason)

- comms/ as an artifact-organization and attention adopter: its ack lifecycle is not contracted (`TreePolicy("comms", ..., "own ack lifecycle not contracted here")`), a separate migration.
  - Carrier: oxjt1d
- walkthroughs/ adoption: no lifecycle status (OQ8 of spec `20260808-1945-01`).
  - Carrier: oxjt1d
- mc5xts part 2, an optional persisted attention snapshot: OQ9 keeps it out until a non-CLI consumer exists.
  - Carrier: mc5xts
- mc5xts part 3, a native plans `executing` state: a plans-owner change (OQ5), unrelated to prompts.
  - Carrier: mc5xts
- `aw archive prompts` weekly shards: 17 files total, no scale pain (P6, no speculative structure).
  - Carrier-Declined: corpus too small to need cold shards; revisit when the plans-sized pain appears.
- A dedicated `find` backend for prompts: `aw find prompts --status executed` already resolves through the generic selector path (measured).
  - Carrier-Declined: already works; a backend would duplicate it.

## Scope check

- Over-scope: none; comms/walkthroughs/snapshot/executing are deferred.
- Under-scope: the plan does not migrate the 8 legacy comment-less prompts (nor the 8 further prompts whose comment carries no `Id:`) to carry metadata; ALL 17 are grandfathered by `PROMPT_ID6_CUTOVER_DATE` and their disposition fully determines their attention class, so nothing is owed for the view to be correct. Stated precisely because the consequence is that two of E-07's three rules govern only FUTURE prompts.
- Also under-scope as authored, now fixed: the item ORDER created a three-item window in which a shipped guard would fail (F-9); the record builder's handling of the near-universal empty id was unstated (F-7); the two zero-subject validator rules were presented as if live output would evidence them (F-8); and E-05 named `ScanRootClassificationInvariantTests`, which does not exist in this repository — the real guard is `tests/test_attention_contract.py::TrackedTreeScanCoverageTests`, and the stale name survives only as a comment inside `artifact_core.py` pointing at an absent `tests/test_artifact_core.py`.

## Required tests / validation

New `tests/test_prompts_attention.py` and `tests/test_prompts_index.py`, each shown FAILING before the implementation; edits to `tests/test_attention_contract.py` and `tests/test_check_engine.py`; live `aw attention --check`, `aw index prompts --check`, `aw check prompts`; bare `python3 -m pytest`.

## Spec / documentation sync

Two implemented specs are AMENDED, declared in Scope-Paths: `20260808-1945-01` (attention registry) because its OQ3 says prompts are deferred to Phase 3 and this plan tracks them, which changes the tree inventory every attention reviewer reads; and `20260730-2152-01` (artifact organization) because Section 7 item 3 marks prompts DONE on naming alone and should record the manifest and check. The plans-adopter spec `20260808-0004-01` is the MODEL reused (`plans_index` shape) and needs no edit. `.aw/records/prompts/README.md` gains the index/attention paragraph.

## Open questions

### OQ-01: Which attention class does a `reusable/` prompt get?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: The question is decided INSIDE this plan's own diff either way (it is one entry of `_PROMPTS_MAP`), and it leaves no work behind it: `reusable/` holds zero prompts, so neither answer changes any live output, and the map entry plus E-02's assertion record whichever choice is made. There is no outstanding obligation for a backlog item or successor plan to own; a maintainer preferring plans-parity flips one dict value and one test expectation.
- Resolution or deferral rationale: Default `parked`. A reusable prompt is a standing runbook, not queued work, and `ready` would list it forever on the default board. Counter-evidence, verified at review: `_PLANS_MAP` really does map plans `reusable` to `READY`, so the two trees would disagree on the same word. `reusable/` is empty today (measured: zero `.prompt.md` files), so either choice changes no live output; flip one map entry and E-02's expectation if the maintainer prefers parity with plans. NOTE the choice is not purely cosmetic for the future: `parked` items are auto-hidden from the default board, so a standing prompt runbook would need `aw attention --all` to be seen, which is the behavior the default is chosen FOR.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the outputs of `python3 -m agent_workflows index prompts`, `python3 -m agent_workflows attention -t prompts --format json` (valid + item count), `python3 -m agent_workflows attention --format json` (valid + count), the per-file disposition/comment table with its row count, the comment-carrying vs comment-less split, the count of prompts declaring an `Id:`, and both `index plans|research --check` outputs. State every number as MEASURED NOW and name any that differs from the figures in E-01, treating a differing count as recorded drift rather than a failure. Confirm explicitly that the two `Status:`-vs-bucket mismatches are still the two files named in `- Scope-Paths:`; if they are not, that IS a structural change and a stop.
  - Observed evidence: Verified baseline: `python3 -m agent_workflows index prompts` returned "WARN 'index' is not supported for prompts."; `python3 -m agent_workflows attention -t prompts --format json` returned `{"valid": true, "items": []}`; whole-view count was `valid: True, count: 1540` matching review; 17 prompts (2 pending, 13 executed, 2 superseded); 9 with `aw-prompt` comment, 8 without; 1 declared id (`ng0ga4`); 2 status mismatches were exactly the 2 files named in Scope-Paths; index plans/research --check drift baseline captured.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_prompts_attention.py -q` run BEFORE E-03..E-05, showing FAILURES (expect assertion errors on `TRACKED_TREES` and `UnknownNativeStatus` for `class_of("prompts", "pending")`), with the failing test names, and confirm the failures are ASSERTIONS rather than a collection or import error. Also confirm the fixture's id distribution matches the live corpus shape (at least one prompt with an `Id:`, at least two without, one of those with no comment at all) and that the bucketed README case is present.
  - Observed evidence: Verified `tests/test_prompts_attention.py` failed before implementation with assertion/contract errors: `AssertionError: assert 'prompts' in {'backlog', 'plans', 'releases', 'research', 'specs'}` and `UnknownNativeStatus: Unknown native status 'pending' for tree 'prompts'` (2 failed, 3 passed in 0.12s); fixture has 1 prompt with Id (`ng0ga4`), 2 without Id (1 with comment, 1 without comment), and 1 bucketed README asserting no item created.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `python3 -c "from agent_workflows import artifact_core as c; print([r for r in c.SCAN_ROOTS if 'prompt' in r])"` showing both new roots beside the pre-existing `prompt-library`; `python3 -m pytest -o addopts="" tests/test_attention_contract.py -q` PASSING (this is the ordering proof: the guard must be green while `prompts` is still untracked); and the `index plans --check` / `index research --check` outputs compared LINE-FOR-LINE with V-01's capture, with any new line explained as a genuine broken citation or the item reported as a stop.
  - Observed evidence: Verified `SCAN_ROOTS` has `['.aw/records/prompt-library', '.agents/prompts', '.aw/records/prompts']`; `python3 -m pytest -o addopts="" tests/test_attention_contract.py -q` passed (26 passed in 0.17s) while prompts was still untracked; `index plans --check` and `index research --check` outputs matched V-01 line-for-line with zero new findings.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste `python3 -c "from agent_workflows import attention_contract as A; print([A.class_of('prompts',s) for s in ('pending','executed','superseded','not-executed','reusable')], 'prompts' in A.TRACKED_TREES, [p.tracked for p in A.TREE_POLICY if p.name=='docs-prompts'])"`, expected `['ready', 'done', 'parked', 'parked', 'parked'] True [False]`; AND `python3 -m pytest -o addopts="" tests/test_attention_contract.py -k TrackedTreeScanCoverage -q` PASSING, which is the assertion that would have been RED for three items under the authored ordering and is the whole reason E-03 precedes E-04.
  - Observed evidence: Verified `python3 -c "from agent_workflows import attention_contract as A; print([A.class_of('prompts',s) for s in ('pending','executed','superseded','not-executed','reusable')], 'prompts' in A.TRACKED_TREES, [p.tracked for p in A.TREE_POLICY if p.name=='docs-prompts'])"` output `['ready', 'done', 'parked', 'parked', 'parked'] True [False]`; `TrackedTreeScanCoverage` test passed (1 passed, 25 deselected in 0.11s).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste the `_prompts_record` diff; `python3 -m pytest -o addopts="" tests/test_prompts_attention.py` fully passing, naming the record, empty-id, missing-status, bucketed-README, and untracked-exclusion cases; and `python3 -m agent_workflows attention -t prompts --format json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['valid'], len(d['items']), sorted({i['attention_class'] for i in d['items']}))"`, expected `True 17` with classes including `ready`. State how many of the 17 items carry an EMPTY id (expected 16 at review's measurement), which is the check that an absent `aw-prompt` comment is handled as normal rather than as drift. Also paste `python3 -m agent_workflows attention --check` exit status, since this is the first item that changes the whole-view content.
  - Observed evidence: Verified `_prompts_record` added to `agent_workflows/attention.py` and dispatched in `_record_for`; `tests/test_prompts_attention.py` 5 passed in 0.13s; `aw attention -t prompts --format json` yielded `True 17 ['done', 'parked', 'ready']` with exactly 16 empty ids (1 declared id: `ng0ga4`); `aw attention --check` exited 0 ("aw attention --check: the view is valid.").
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste `tests/test_prompts_index.py` FAILING before `prompts_index.py` exists (ModuleNotFoundError or equivalent), then passing; then `python3 -m agent_workflows index prompts` (writes two files), `python3 -m agent_workflows index prompts --check` printing clean, and `git check-ignore -v .aw/records/prompts/INDEX.json .aw/records/prompts/INDEX.md` naming the `.aw/.gitignore` lines.
  - Observed evidence: Verified `tests/test_prompts_index.py` failed with `ModuleNotFoundError` before `prompts_index.py` was created and passed (8 passed in 0.20s) after; `aw index prompts` wrote `INDEX.json` (17 prompts) and `INDEX.md`; `aw index prompts --check` reported `prompts index --check: clean`; `git check-ignore -v .aw/records/prompts/INDEX.json .aw/records/prompts/INDEX.md` confirmed lines 49-50 of `.aw/.gitignore`.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: paste the validator tests FAILING before the `check_content` branch is added and passing after, and `python3 -m agent_workflows check prompts --agent` BEFORE E-08 showing exactly two `check.prompt-status-mismatch` diagnostics naming the two files AND ZERO `check.prompt-metadata-missing` / `check.prompt-id-mismatch` diagnostics, plus `grep -n 'SUPPORTED' -A9 agent_workflows/check_engine.py` showing `"prompts": ("names", "content")`. SEPARATELY paste the FIXTURE evidence for the two rules that have no live subjects: a synthetic post-cutover-dated prompt with no `aw-prompt` comment producing `check.prompt-metadata-missing`, and a comment `Id:` differing from a clustered filename's id6 producing `check.prompt-id-mismatch`. Do NOT report their absence from live output as evidence that they work; `_prompt_requires_id6` returns False for every current file, so live silence is the expected no-op and proves nothing.
  - Observed evidence: Verified `SUPPORTED["prompts"] = ("names", "content")`; `python3 -m agent_workflows check prompts --agent` before E-08 reported outcome `refused` with exactly two `check.prompt-status-mismatch` diagnostics for the 2 scope files and 0 `check.prompt-metadata-missing` / `check.prompt-id-mismatch` diagnostics; synthetic fixture tests in `tests/test_prompts_index.py` (`test_check_content_prompt_metadata_missing_post_cutover`, `test_check_content_prompt_id_mismatch`, `test_check_content_prompt_status_mismatch`) pass and verify all three rules.
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: paste `git diff --stat` for the two prompt files (1 line changed each) and `python3 -m agent_workflows check prompts --agent` showing `outcome":"conforms` with no `check.prompt-` diagnostic.
  - Observed evidence: Verified `git diff --stat .aw/records/prompts/executed/` showed 2 files changed, 2 insertions(+), 2 deletions(-); `python3 -m agent_workflows check prompts --agent` output `{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"prompts","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":null}` (0 `check.prompt-*` diagnostics).
  - Result: pass
- [x] V-09 validates E-09
  - Required evidence: paste `git diff` hunks for both specs and the README, and `grep -n 'deferred to Phase 3' agent_workflows/attention_contract.py` showing only the comms entry remains.
  - Observed evidence: Verified specs `20260808-1945-01` (OQ3 amended) and `20260730-2152-01` (Section 7 item 3 updated) and `.aw/records/prompts/README.md` (Index and attention section added) updated per diff; `grep -n 'deferred to Phase 3' agent_workflows/attention_contract.py` shows only comms remains deferred to Phase 3.
  - Result: pass
- [x] V-10 validates E-10
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` (the `N passed` line, zero failed), the `python3 -m agent_workflows attention --check` exit status 0, and `python3 -m agent_workflows check prompts` showing 0 errors.
  - Observed evidence: Verified `python3 -m pytest` full bare suite: `2078 passed, 1 skipped, 3 warnings in 35.04s`; `python3 -m agent_workflows attention --check` printed `aw attention --check: the view is valid.` (exit 0); `python3 -m agent_workflows check prompts` printed `✓ CONFORMS  2 prompts checked` (exit 0, 0 prompt errors).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make staged prompts a full artifact-organization and attention adopter). E-03, E-04 and E-05 are three items rather than one because the ORDER between them is load-bearing (F-9) and each has distinct evidence: a scan-root widening proven inert, a policy flip proven not to break the coverage guard, and a record builder proven to handle the near-universal empty id. E-07 and E-08 are separate because the validator's live output BEFORE the reconciliation is the evidence that the rule works at all.

WHAT A HUMAN IS APPROVING. Adding a whole tree to `aw attention`, which changes what `/whatnext` shows every reader, and AMENDING TWO IMPLEMENTED SPECS whose text currently says prompts are deferred. Three things are worth an explicit look. FIRST, the two queued prompts in `pending/` will start appearing as `ready` work on the default board; that is the point of the plan, and it is a change to a surface people read daily. SECOND, two of the three new content rules govern only prompts created after `PROMPT_ID6_CUTOVER_DATE` and fire on ZERO current files (F-8), so `aw check prompts` gains real coverage for the future and almost none for the present; approving this is approving a forward-looking guard, not a cleanup of existing metadata. THIRD, OQ-01 (`reusable` -> `parked` versus plans-parity `ready`) is a live judgement the maintainer may overrule with a one-line change, and it currently affects no file because `reusable/` is empty.

SCOPE FENCE (a declaration, so the runner can reconcile afterwards; not an instruction to stop over a scope question). Within the declared paths the intended surface is: `artifact_core.py` the `SCAN_ROOTS` tuple only; `attention_contract.py` the `prompts` `TreePolicy`, the new `_PROMPTS_MAP`, its `CLASS_MAPS` entry, and the v1-scope comment only, leaving `docs-prompts` and `comms` excluded; `attention.py` the new `_prompts_record` plus its `_record_for` dispatch only; `artifact_types.py` the `prompts` `TYPE_BACKENDS` entry only; `check_engine.py` the `SUPPORTED["prompts"]` value, the new `check_content` branch, and the three `RULE_REGISTRY` entries only; `prompts_index.py` NEW; `engine.py` the anchored gitignore pattern tuple only; `.aw/.gitignore` two added lines; the two prompt files' `Status:` field ONLY, bodies byte-identical; the two specs' named paragraphs; the prompts README's new paragraph; and the four test files. DELIBERATELY NOT IN SCOPE, mirroring Deferred: `comms`/`walkthroughs` adoption, the persisted attention snapshot, a plans `executing` state, `aw archive prompts` shards, a prompts `find` backend, migrating the 16 prompts that declare no id6, and the `prompts` `TreePolicy.root` spelling. An out-of-scope edit that proves necessary should be MADE and then justified with `--scope-reason` at finalize.

HONESTY RULE (hard MUST). Paste the ACTUAL command output for every `V-*` item. Three specific temptations to refuse: do not report the live absence of `check.prompt-metadata-missing` / `check.prompt-id-mismatch` findings as evidence those rules work, since `_prompt_requires_id6` is False for every current file and silence is the expected no-op (V-07 requires fixture evidence instead); do not absorb a changed corpus COUNT into the authored figures, since the whole-view total already moved 1508 -> 1540 between authoring and review; and do not run V-03's `test_attention_contract.py` check after E-04, because its whole purpose is to prove the guard is green while `prompts` is still untracked.

STOP CONDITIONS (genuinely unsafe, distinct from a scope question). Stop and report if: E-01 finds a STRUCTURAL change (an index backend now exists, the tree is already tracked, or the two `Status:` mismatches are already reconciled), because the plan's premise has moved; E-03's re-run shows a NEW dangling citation that is not a genuine broken citation in a prompt file already declared; or a spec paragraph E-09 must amend has been rewritten under you by concurrent work.

Execute only after explicit human approval (`- Status: approved`). Commit through `aw commit dx0u4s -- <paths>` limited to Scope-Paths; never push. After every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, the lifecycle transition to `executed/` is performed by the RUNNER when one is driving this plan, and by the executor via `aw ipd finalize` only when no runner owns the transition; do not hand-roll a `git mv`. Backlog `oxjt1d` carries no `- Blocks-Release:`, so no release gate is owed and none may be invented; `mc5xts` stays open, since this plan graduates only its first part.
