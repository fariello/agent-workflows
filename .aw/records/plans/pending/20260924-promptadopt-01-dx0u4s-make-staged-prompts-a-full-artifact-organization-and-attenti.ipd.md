# IPD: Make staged prompts a full artifact-organization and attention adopter

- Date: 2026-09-24
- Kind: child
- Concern: Graduates backlog `oxjt1d` (apply the artifact-organization model to `prompts/` reusing `artifact_core`) AND the first part of `mc5xts` (prompts as a Phase-3 attention adopter). MEASURED, the NAMING half of `oxjt1d` is ALREADY DONE: IPD `ubac5n` made staged prompts carry `<id6>` in the name and in the `<!-- aw-prompt: ... -->` comment, `check_engine._prompt_requires_id6` enforces it from cutover `20260921`, and spec `20260730-2152-01` Section 7 item 3 already reads "`prompts/`: DONE (`promptid6` `ubac5n`...)". What is NOT done is everything else the model promises: `aw index prompts` prints "WARN 'index' is not supported for prompts." (`artifact_types.TYPE_BACKENDS["prompts"]` has only `new`/`rename`/`group`); `check_engine.SUPPORTED["prompts"]` is `("names",)` with the comment "prompts / walkthroughs / roadmaps: no content validator today"; and `attention_contract.TREE_POLICY` still carries `TreePolicy("prompts", ".agents/prompts", False, "", "deferred to Phase 3 (OQ3)...")`, while `core.SCAN_ROOTS` lists no `.aw/records/prompts`, so `aw attention -t prompts --format json` reports `valid: true` with ZERO items over a 17-file corpus with 2 queued prompts in `pending/`.
- Scope: PROMPTS ONLY. IN: (a) attention adoption: flip the `prompts` TreePolicy to tracked, add a pure/total `_PROMPTS_MAP` over the prompt DISPOSITION enum, add the scan root, add a `_prompts_record` builder; (b) a generated, gitignored `INDEX.json`/`INDEX.md` manifest with `--check` via a new `prompts_index` module reusing `artifact_core`; (c) a prompts CONTENT validator so `aw check prompts` checks metadata, not just names; (d) reconcile the 2 live metadata/disposition mismatches; (e) amend the two specs whose text says prompts are deferred. OUT: comms and walkthroughs adoption, `mc5xts`'s persisted snapshot and plans `executing` state, prompt archive shards (see Deferred).
- Scope-Paths: agent_workflows/attention_contract.py, agent_workflows/attention.py, agent_workflows/artifact_core.py, agent_workflows/artifact_types.py, agent_workflows/check_engine.py, agent_workflows/prompts_index.py, agent_workflows/engine.py, .aw/.gitignore, .aw/records/prompts/README.md, .aw/records/prompts/executed/20260808-1948-01-attention-registry-spec-external-review.prompt.md, .aw/records/prompts/executed/20260828-2156-01-research-worktree-isolation-state-model.prompt.md, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md, tests/test_prompts_attention.py, tests/test_prompts_index.py, tests/test_attention_contract.py, tests/test_check_engine.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: low
- Set: promptadopt
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: dx0u4s
- From-Backlog: oxjt1d

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog oxjt1d, mc5xts (first part only: prompts as attention adopters); re-measured that prompt naming/id6 is already done (`ubac5n`) while `aw index prompts` is unsupported, `aw check prompts` is names-only, and `aw attention -t prompts` yields 0 items because the tree is excluded and unscanned.

## Goal

Make `.aw/records/prompts/` a first-class adopter of the artifact-organization model beyond naming (manifest + content check) and a TRACKED attention tree, so the two queued prompts in `pending/` surface as `ready` in `aw attention` and `/whatnext` instead of being invisible.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline and failing tests first

- [ ] E-01 RE-MEASURE the baseline before changing anything: `python3 -m agent_workflows index prompts` (expect "'index' is not supported for prompts"), `python3 -m agent_workflows attention -t prompts --format json` (expect `valid: true`, 0 items), `python3 -m agent_workflows attention --format json` (record `valid` and total item count; at authoring `True 1508`), and the per-file disposition-vs-comment table (at authoring: 17 prompts; 8 carry the `aw-prompt` comment; 2 in `executed/` still say `Status: pending`: `20260808-1948-01-attention-registry-spec-external-review` and `20260828-2156-01-research-worktree-isolation-state-model`). Also record the dangling-citation baseline: `python3 -m agent_workflows index plans --check` and `python3 -m agent_workflows index research --check` output, because E-05 widens `SCAN_ROOTS`, which those checks consume. If any claim moved, STOP and report.
  - Depends on: none
  - Expected outcome: pasted baseline outputs; any drift from the authoring numbers reported rather than absorbed.
  - Execution state: pending

- [ ] E-02 WRITE `tests/test_prompts_attention.py` BEFORE the implementation, over a temp fixture repo (`.aw/records/prompts/{pending,executed,superseded,not-executed,reusable}/` plus one `untracked/` file): assert `attention_contract.class_of("prompts", s)` for every disposition per the Findings table; assert `"prompts" in attention_contract.TRACKED_TREES`; assert `attention.scan(root)` yields one `prompts` item per bucketed prompt with the id6 read by `prompts.read_metadata_id6` (empty id for a legacy comment-less file), a `pending/` prompt classed `ready`, and the `untracked/` file ABSENT; assert a prompt placed directly under `.aw/records/prompts/` (no bucket) yields `attention.missing-status`. Run it and capture the FAILURES.
  - Depends on: E-01
  - Expected outcome: new test module exists and fails against unchanged code.
  - Execution state: pending

### Task group 2: attention adoption (mc5xts part 1)

- [ ] E-03 In `agent_workflows/attention_contract.py`: change the `prompts` `TreePolicy` to `tracked=True`, owner `"aw prompts"`, reason naming the disposition-as-status contract; add `_PROMPTS_MAP` = `{pending: READY, executed: DONE, superseded: PARKED, not-executed: PARKED, reusable: PARKED}` per OQ-01 and register it in `CLASS_MAPS`; update the "v1 scope (OQ3)" comment above `TREE_POLICY` to say prompts are tracked (comms still deferred). Leave `docs-prompts` (the prompt LIBRARY) excluded.
  - Depends on: E-02
  - Expected outcome: `class_of` is total over the prompt disposition enum; `docs-prompts` still excluded.
  - Execution state: pending

- [ ] E-04 In `agent_workflows/attention.py`: add `_prompts_record(rel, path, text)` and dispatch it from `_record_for`. The NATIVE STATUS IS THE DISPOSITION DIRECTORY (first path component under `.aw/records/prompts/` or `.agents/prompts/`, alias `done` normalized to `executed`), mirroring `_plan_disposition_from_rel`, because the prompts README states "its lifecycle is tracked by MOVING it between the buckets" and 9 of 17 files carry no in-file status at all. The id comes from `prompts.read_metadata_id6(text)`. A file with no bucket emits `attention.missing-status`; an unknown bucket emits `attention.unknown-status`. Do NOT read the comment `Status:` here (that disagreement is `aw check prompts`'s job, E-07).
  - Depends on: E-03
  - Expected outcome: `_record_for("prompts", ...)` returns an `Item` for every bucketed prompt.
  - Execution state: pending

- [ ] E-05 In `agent_workflows/artifact_core.py`, add `".aw/records/prompts"` and `".agents/prompts"` to `SCAN_ROOTS` with a comment citing this plan (the `releases` precedent: a tracked tree with no scan root is invisible while the view reports valid). Then re-run the E-01 dangling-citation checks; if the widened root produces NEW dangling findings, fix only those that are genuine broken citations in prompt files you declared, otherwise STOP and report the list.
  - Depends on: E-04
  - Expected outcome: `aw attention -t prompts` lists the prompts; `ScanRootClassificationInvariantTests` stays green; dangling-citation counts unchanged or explained.
  - Execution state: pending

### Task group 3: manifest and content check (oxjt1d)

- [ ] E-06 WRITE `tests/test_prompts_index.py` first (fixture repo as in E-02): `build_index_json` lists every bucketed prompt with `id6`/`set`/`order`/`disposition`/`kind`; `check_drift` reports `check.stale-index-missing` (info, exit 0) when absent, `check.stale-index-stale` when the on-disk JSON is edited, and `name-metadata-mismatch` when a clustered filename's id6 differs from the comment `Id:`. Capture failures (module absent). Then create `agent_workflows/prompts_index.py` modeled on `plans_index` (`scan_prompts`, `build_index_json`, `build_index_md`, `check_drift`, `run_index`), reusing `artifact_core.Drift`/`drift_exit_code`/`atomic_write` and `artifact_naming.parse_clustered`, stamping severity via `check_engine.enrich_drift` exactly as `plans_index.check_drift` does. Wire `"index": "prompts_index.run_index"` into `artifact_types.TYPE_BACKENDS["prompts"]`. Add `records/prompts/INDEX.json` and `records/prompts/INDEX.md` to `.aw/.gitignore` and to the anchored pattern tuple in `engine.py` beside the four existing `records/plans|research/INDEX.*` lines (the `ueg5cf` merge-conflict reason applies unchanged).
  - Depends on: E-05
  - Expected outcome: `aw index prompts` writes two gitignored files; `aw index prompts --check` clean after a rebuild.
  - Execution state: pending

- [ ] E-07 Add a prompts content validator in `check_engine.check_content` and change `SUPPORTED["prompts"]` to `("names", "content")`. Rules (register each in `RULE_REGISTRY`): `check.prompt-metadata-missing` (error) for a prompt whose name requires id6 per `_prompt_requires_id6` but whose first line is not an `aw-prompt` comment (pre-cutover files are grandfathered, which covers all 9 comment-less files); `check.prompt-id-mismatch` (error) when a comment `Id:` differs from the filename id6; `check.prompt-status-mismatch` (warning) when the comment `Status:` names a terminal disposition different from the bucket, or says `pending` inside a terminal bucket. Add the cases to `tests/test_prompts_index.py` (or a class in `tests/test_prompts_attention.py`), and update the `"content over prompts, a type with NO content validator"` row rationale in `tests/test_check_engine.py::EntryPointTests` (its expected `()` still holds because that shared tree has no prompts; the prose must stop claiming no validator exists).
  - Depends on: E-06
  - Expected outcome: `aw check prompts` reports exactly the 2 live `check.prompt-status-mismatch` findings before E-08.
  - Execution state: pending

- [ ] E-08 Reconcile the two live mismatches by editing ONLY the `Status:` field inside the leading `aw-prompt` comment of `20260808-1948-01-attention-registry-spec-external-review.prompt.md` and `20260828-2156-01-research-worktree-isolation-state-model.prompt.md` from `pending` to `executed` (their directory is the authority). Leave every prompt body byte-identical.
  - Depends on: E-07
  - Expected outcome: `aw check prompts` exits 0 with no `check.prompt-*` findings.
  - Execution state: pending

### Task group 4: spec and docs sync, full suite

- [ ] E-09 Amend the specs and README: append a dated AMENDED note to spec `20260808-1945-01` beside OQ3 recording that prompts are now a tracked tree with the disposition map (comms still deferred to Phase 3); extend spec `20260730-2152-01` Section 7 item 3 to say the manifest and content check landed (plan `dx0u4s`), `comms/`/`walkthroughs/` still subsequent; add an "Index and attention" paragraph to `.aw/records/prompts/README.md` naming `aw index prompts [--check]`, `aw check prompts`, and the class mapping. Update `tests/test_attention_contract.py` so any assertion that prompts is excluded or unmapped reflects the new contract (the `class_of("prompts", "anything")` raise stays valid).
  - Depends on: E-08
  - Expected outcome: no spec or README text still says staged prompts are deferred or unindexed.
  - Execution state: pending

- [ ] E-10 Run the bare suite `python3 -m pytest` with no extra flags, then `python3 -m agent_workflows attention --check` and `python3 -m agent_workflows check prompts`.
  - Depends on: E-09
  - Expected outcome: suite green; view valid; prompts check clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A prompt's metadata lives in ONE leading HTML comment, never a `- Id:` bullet (spec `20260808-1958-01-prompt-purity-lint` R1/P4, restated in `prompts.py` module docstring). So the attention record must read the id via `prompts.read_metadata_id6`, not `_plans_id`.
- Generated manifests are GITIGNORED, anchored per path, and a missing one is `info` (`plans_index.check_drift` comment "idxuntrack 02 (yvvf98)"; `.aw/.gitignore` "Written as four ANCHORED specific paths").
- `class_of` must be PURE and TOTAL over the native enum and the scanner may not infer state from prose (spec `20260808-1945-01` Section 6, quoted in the `reviews` TreePolicy comment).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Naming/id6 adoption already done | `prompts.py` docstring "IPD `ubac5n`"; spec `20260730-2152-01` Section 7 item 3 "DONE" |
| F-2 | No index backend | `aw index prompts` -> "WARN 'index' is not supported for prompts." |
| F-3 | Names-only check | `check_engine.SUPPORTED["prompts"] = ("names",)` |
| F-4 | Tree excluded and unscanned | `TreePolicy("prompts", ".agents/prompts", False, ...)`; `.aw/records/prompts` absent from `artifact_core.SCAN_ROOTS`; attention `-t prompts` gives 0 items |
| F-5 | Disposition is the reliable status | 9 of 17 files have no `aw-prompt` comment; 2 of 8 that do disagree with their bucket |
| F-6 | Existing lifecycle vocabulary | `lifecycle_style._PROMPTS_PAIRS`: pending READY, executed DONE, reusable REUSABLE, superseded SUPERSEDED, not-executed ABANDONED |

Proposed class mapping (disposition -> attention class): pending -> ready; executed (and alias done) -> done; superseded -> parked; not-executed -> parked; reusable -> parked (OQ-01).

## Proposed changes (ordered, validatable)

1. Baseline (E-01) and failing attention tests (E-02).
2. Contract map + tracked policy (E-03), record builder (E-04), scan root (E-05).
3. `prompts_index` manifest with `--check`, wired and gitignored (E-06).
4. Content validator and rules (E-07); fix the two live mismatches (E-08).
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
- Under-scope: the plan does not migrate the 9 legacy comment-less prompts to carry metadata; they are grandfathered pre-cutover and their disposition fully determines their class.

## Required tests / validation

New `tests/test_prompts_attention.py` and `tests/test_prompts_index.py`, each shown FAILING before the implementation; edits to `tests/test_attention_contract.py` and `tests/test_check_engine.py`; live `aw attention --check`, `aw index prompts --check`, `aw check prompts`; bare `python3 -m pytest`.

## Spec / documentation sync

Two implemented specs are AMENDED, declared in Scope-Paths: `20260808-1945-01` (attention registry) because its OQ3 says prompts are deferred to Phase 3 and this plan tracks them, which changes the tree inventory every attention reviewer reads; and `20260730-2152-01` (artifact organization) because Section 7 item 3 marks prompts DONE on naming alone and should record the manifest and check. The plans-adopter spec `20260808-0004-01` is the MODEL reused (`plans_index` shape) and needs no edit. `.aw/records/prompts/README.md` gains the index/attention paragraph.

## Open questions

### OQ-01: Which attention class does a `reusable/` prompt get?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default `parked`. A reusable prompt is a standing runbook, not queued work, and `ready` would list it forever on the default board. Counter-evidence: `_PLANS_MAP` maps plans `reusable` to `READY`. `reusable/` is empty today, so either choice changes no live output; flip one map entry if the maintainer prefers parity with plans.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the outputs of `python3 -m agent_workflows index prompts`, `python3 -m agent_workflows attention -t prompts --format json` (valid + item count), `python3 -m agent_workflows attention --format json` (valid + count), the 17-row disposition/comment table, and both `index plans|research --check` outputs; state any number that differs from the authoring figures.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_prompts_attention.py -q` run BEFORE E-03..E-05, showing FAILURES (expect assertion errors on `TRACKED_TREES` and `UnknownNativeStatus` for `class_of("prompts", "pending")`), with the failing test names.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -c "from agent_workflows import attention_contract as A; print([A.class_of('prompts',s) for s in ('pending','executed','superseded','not-executed','reusable')], 'prompts' in A.TRACKED_TREES, [p.tracked for p in A.TREE_POLICY if p.name=='docs-prompts'])"`, expected `['ready', 'done', 'parked', 'parked', 'parked'] True [False]`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the `_prompts_record` diff and the output of `python3 -m pytest -o addopts="" tests/test_prompts_attention.py -k record` showing the record, missing-status, and untracked-exclusion cases PASS.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m agent_workflows attention -t prompts --format json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['valid'], len(d['items']), sorted({i['attention_class'] for i in d['items']}))"`, expected `True 17` and classes including `ready`; the full `tests/test_prompts_attention.py` and `tests/test_attention_contract.py` passing; and the post-change `index plans|research --check` outputs compared line-for-line with V-01.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `tests/test_prompts_index.py` FAILING before `prompts_index.py` exists (ModuleNotFoundError or equivalent), then passing; then `python3 -m agent_workflows index prompts` (writes two files), `python3 -m agent_workflows index prompts --check` printing clean, and `git check-ignore -v .aw/records/prompts/INDEX.json .aw/records/prompts/INDEX.md` naming the `.aw/.gitignore` lines.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the validator tests FAILING before the `check_content` branch is added and passing after, and `python3 -m agent_workflows check prompts --agent` BEFORE E-08 showing exactly two `check.prompt-status-mismatch` diagnostics naming the two files, plus `grep -n 'SUPPORTED' -A9 agent_workflows/check_engine.py` showing `"prompts": ("names", "content")`.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste `git diff --stat` for the two prompt files (1 line changed each) and `python3 -m agent_workflows check prompts --agent` showing `outcome":"conforms` with no `check.prompt-` diagnostic.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste `git diff` hunks for both specs and the README, and `grep -n 'deferred to Phase 3' agent_workflows/attention_contract.py` showing only the comms entry remains.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` (the `N passed` line, zero failed), the `python3 -m agent_workflows attention --check` exit status 0, and `python3 -m agent_workflows check prompts` showing 0 errors.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit dx0u4s -- <paths>` limited to Scope-Paths; never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence.
