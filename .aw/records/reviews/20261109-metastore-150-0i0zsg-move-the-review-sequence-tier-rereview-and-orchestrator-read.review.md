# Review: 0i0zsg - Move the review sequence, tier, rereview and orchestrator readiness reads onto artifact_meta

- Subject-Id: 0i0zsg
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

#### Changes
- Replaced the raw authoring instruction in the blockquote preamble with a conformance statement (`PR-007`).
- Expanded `## Proposed changes (ordered, validatable)` so each numbered item names its target modules, moved symbols, and baseline diff, and added a Requirement 12(b) `mermaid` `flowchart TD` diagram covering prerequisites, `E-01`, `V-01`, `E-02`, and `V-02` with a one-sentence ordering rationale (`PR-007`).
- Rewrote `## Findings` (`F-02` and `READER LEDGER`) so every reader site is attributed to an explicit `module.function` symbol (`IPD-C801`) and re-verified at `537a13f3e`.
- Added `## Behavior decisions (kept or changed behavior, 4.3)` (`D-1` to `D-3`) so snapshot field mappings, derived-id fallbacks, and cached-path joins are explicit rather than left to executor inference.
- Changed `OQ-01` `- Owner: none` to `- Owner: plan author` (`PR-008`).

#### Issues
- None remaining after revision; checked against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`. Zero em or en dashes appear in the plan or this review record (`IPD-C802`). Recommendation strength for remaining prose conformance: strong.

### Step T

1. Yes. Implements spec `4sd62s` C5a across four modules (`review_sequence`, `review_tier`, `review_rereview`, `orchestrator_readiness`) that form the cross-module multi-prompt review runner, tiering, re-review trigger, and orchestrator coverage-gate interfaces, consuming `artifact_meta.read`, `query`, `resolve`, `read_text`, `restore_legacy_snapshot`, and `source_path`.
2. Yes. `orchestrator_readiness` (`review_readiness`, `run_coverage`) backs the orchestrator coverage gate (`IPD-M112`, `aw ipd set`, and runner retirement refusals), and `review_sequence` (`structural_diff`, `check_S5`, `check_S7`, `restore_pre_s7_plan`) enforces multi-prompt review structural preservation and pre-S7 verdict guards.
3. Small-to-moderate. 2 `E-*` items in 1 task group across 4 production modules, 1 shared reader-pinning test module, and 5 baseline test modules (63 existing tests).
4. Yes. 5 work `Scope-Paths` (`agent_workflows/review_sequence.py`, `agent_workflows/review_tier.py`, `agent_workflows/review_rereview.py`, `agent_workflows/orchestrator_readiness.py`, `tests/test_readers_review_modules.py`) plus the plan file itself; complete and narrow once the `history_block` text grammar calls in `review_sequence` are confirmed deferred to `ay6sxp`.
5. High. A subtle mismatch in `structural_diff`, `tier_facts`, `rereview_triggers`, `restore_pre_s7_plan`, or `orchestrator_readiness` could silently drop re-review triggers, reject valid proofreading passes, corrupt pre-S7 snapshot restoration, or mis-classify orchestrator set membership during unattended runs.

AW-TIER: complex

### Step R1

- Checked: `agent_workflows/review_sequence.py` (`structural_diff`, `check_S5`, `count_verdict_bearing_entries`, `verdict_outputs`, `restore_pre_s7_plan`, `check_S7`), `agent_workflows/review_tier.py` (`tier_facts`, `render_tier_facts`), `agent_workflows/review_rereview.py` (`rereview_triggers`, `check_limit_s7`), `agent_workflows/orchestrator_readiness.py` (`_BATCH_META_RE`, `resolve_all_set_memberships`, `review_readiness`, `run_coverage`), `agent_workflows/artifact_meta.py` (`REGISTRY`, `State`, `load_legacy_artifact`, `read`, `history`, `query`), spec `4sd62s` (C5, C5a, 4.3, N3), and sibling plans `2zpw22`, `y4spqy`, `awmsyq`, `ffceq0`, `cdglt1`, `1suzlp`, `7yr827`, `6oi2nu`, `tdhav3`, `bxupy8`, and `ay6sxp`.
- `E-01` parenthetically listed `count_verdict_bearing_entries` while omitting `structural_diff` and `check_S5` by symbol name. At `537a13f3e`, `review_sequence.count_verdict_bearing_entries` contains zero bullet-metadata reads (`meta_fields` or `read_readiness`); it takes an in-memory snapshot `plan_text: str` and calls `plan_readiness.history_block`, whereas `artifact_meta.history(id6)` queries the on-disk SQLite cache by `id6` and cannot distinguish `plan_text_before` from `plan_text_after` in `check_S7`. Meanwhile `bxupy8` `E-03` (Order 290) adds the public `artifact_meta` text-history entry point and `ay6sxp` `E-02` (Order 291) explicitly moves `plan_readiness.history_block` in `count_verdict_bearing_entries` and `restore_pre_s7_plan`. Fixed in `E-01`, `F-02`, and `## Deferred / out of scope` by naming the exact 5 bullet-metadata functions (`structural_diff`, `check_S5`, `verdict_outputs`, `restore_pre_s7_plan`, `check_S7`) and recording `ay6sxp` as the carrier for `history_block` (`PR-001`). Recommendation strength: very strong.
- All 8 functions moved by `E-01` accept in-memory `str` snapshots rather than on-disk `id6` tokens, so all 8 call `artifact_meta.read_text(text, record_type="ipd")` (`cdglt1` `E-03` via `ffceq0`) rather than `artifact_meta.read`/`query`/`history`. Clarified in `E-01`, `READER LEDGER`, and `D-2` (`PR-003`). Recommendation strength: strong.
- Verified `_BATCH_META_RE` in `agent_workflows/orchestrator_readiness.py` has zero external callers across `agent_workflows/` and `tests/`; `E-02` now names `resolve_all_set_memberships`, `review_readiness`, and `run_coverage` and explicitly deletes `_BATCH_META_RE` (`PR-004`). Recommendation strength: strong.

### Step R2

- Checked: `E-*`/`V-*` bijection (`E-01` <-> `V-01`, `E-02` <-> `V-02`), `- Scope-Paths:` completeness, `- Item-Dependencies:` (`ffceq0`, `g5hpbb`, `h58z9n`, `tve77h`, `xexn45`, `y4spqy`), orchestrator `63ib9r` (`E-89 CONFIRM 0i0zsg REACHED executed`), `ipd_schema.count_named_units`, baseline test run (`63 passed in 8.31s` across the five baseline modules at `537a13f3e`), and finalize gate mechanics.
- `E-01` stated "`restore_pre_s7_plan` still WRITES plan text and is a writer for Order 07; only its reads move here", while `V-01` demands empty `rg` output for `^-` regexes in `agent_workflows/review_sequence.py`. The only two `^-` regexes in `review_sequence.py` are the writer matches inside `restore_pre_s7_plan`, and prerequisite `executed:xexn45` (through `7yr827` `E-04`, Order 21) already moves that write half onto `artifact_meta.restore_legacy_snapshot` before `0i0zsg` executes. Updated `Scope`, `E-01`, and `## Deferred / out of scope` (`Carrier: 7yr827, xexn45`) so an executor keeps `restore_legacy_snapshot` intact and moves only the pre-pass reads, making `V-01` deterministic (`PR-002`). Recommendation strength: very strong.
- Leaving `_BATCH_META_RE = re.compile(r"^- ...")` unused in `agent_workflows/orchestrator_readiness.py` would fail `V-02`'s `rg` assertion; `E-02` now requires deleting `_BATCH_META_RE`, and `V-01` and `V-02` extend their `rg` checks to verify zero residual `meta_fields`, `read_readiness(`, or `_BATCH_META_RE` hits (`PR-004`). Recommendation strength: strong.
- The checklist preamble redirected output to `.aw/state/t4gl15/<file>` without creating `.aw/state/t4gl15/`; because `.aw/state/` is gitignored and `y4spqy` runs in a separate isolated lane worktree, that redirect would fail on a clean lane. Added `mkdir -p .aw/state/t4gl15` and noted preserving `pytestmark = pytest.mark.core` in `tests/test_readers_review_modules.py` (`PR-005`). Recommendation strength: strong.
- `## Approval and execution gate` stated an unconditional `aw ipd finalize` transition without runner-vs-hand ownership or the explicit `never a hand git mv` rule, omitted shared-checkout safety and narrow prerequisite stop conditions, and omitted `aw sanitize --agent` in `## Required tests / validation`. Hardened both sections (`PR-006`). Recommendation strength: strong.

### Step R3

- Checked: path resolution in `orchestrator_readiness` (`resolve_all_set_memberships`, `review_readiness`, `run_coverage`), `artifact_meta.source_path` / `State.id_derived` (`6oi2nu`), pre-S7 snapshot restoration (`restore_pre_s7_plan` -> `artifact_meta.restore_legacy_snapshot` without emitting a `set readiness` event), and leak-sanitizer hygiene.
- No network, credential, secret, or privilege boundary is touched. Using `artifact_meta.source_path` (from `6oi2nu` via `g5hpbb`) keeps extra-root `@repo/` paths bounded inside the repository root (`_check_path_safety`), and skipping `State.id_derived` rows in `resolve_all_set_memberships` and `check_S5` prevents synthetic cache-only derived ids from leaking into review-record snippets (`- Subject-Id:`) or orchestrator set memberships (`D-3`, `PR-003`, `PR-004`). Recommendation strength: strong.

### Step R4

- Checked: existing assertions in `tests/test_review_sequence.py`, `tests/test_review_sequence_runner.py`, `tests/test_review_tier.py`, `tests/test_review_rereview.py`, and `tests/test_orchestrator_readiness.py` against `artifact_meta.REGISTRY["ipd"]` and `load_legacy_artifact` field mappings.
- `artifact_meta.load_legacy_artifact` maps `- Priority:` to lowercase `"priority"`, `- Kind:` to `"plan_role"`, `- Scope-Paths:` to `"scope_paths"`, and `- Item-Dependencies:` to `"item_dependencies"`. In `tests/test_review_sequence.py::test_structural_diff`, `assert "Priority" in refused[0]` requires canonical IPD bullet casing in `structural_diff`'s diagnostic string, and `tests/test_review_tier.py::test_tier_facts_fixtures` plus `test_tier_facts_empty_and_no_metadata` require `tier_facts` to return `None` for `TODO`-prefixed `Scope-Paths` and never raise on empty or headerless text. Recorded these exact mappings and edge-case invariants in `D-2` and `D-3` (`PR-003`, `PR-004`). Recommendation strength: very strong.
- Verified body-prose parsing (`exec_leaves`, `valid_leaves`, `open_questions`, `h2`, `orchestrator_row_conformance`) remains on `ipd_lint.parse` per `4sd62s` N3. Recommendation strength: strong.

### Step R5

- Checked: the eight reviewer personas (QA/QC, testing and regression, UI/UX, architect, software engineer, power user, novice, stakeholder).
- QA/QC and testing: the pin-first `E-12a`/`E-12b` outcome-list diffs over all 63 existing tests plus dedicated `tests/test_readers_review_modules.py` cases catch any casing, `TODO`-scope, or `id_derived` regression immediately, without reading production source.
- Architect and software engineer: naming the exact 8 `E-01` functions and 3 `E-02` functions while keeping each `E-*` item at 7 `count_named_units` preserves `4sd62s` C5a single-reader authority and keeps each step small enough for a single focused pass.
- UI/UX, power user, novice, and stakeholder: CLI outputs (`aw ipd coverage`), multi-prompt review diagnostics (`structural_diff`, `rereview_triggers`), and orchestrator readiness messages remain byte-compatible while advancing `4sd62s` C5a (`Blocks-Release: next`). Recommendation strength: strong.

### Step R6

- Checked: whether `0i0zsg` should be decomposed into its own Set or further child plans.
- No split needed: 2 `E-*` items in 1 task group, 5 work `Scope-Paths`, and 7 named units per `E-*` item (inside `nj8zdp` guidance of at most 5 `E-*` items, 8 work `Scope-Paths`, and 8 units per item). Both items share `tests/test_readers_review_modules.py` and implement `63ib9r` `E-89`. Recommendation strength: strong.

### Step R7

- Checked: parent `2zpw22` (Order 36), siblings `y4spqy` (Order 149) and `awmsyq` (Order 154), prerequisites `ffceq0` / `cdglt1` / `1suzlp`, `g5hpbb` / `6oi2nu`, `h58z9n`, `tve77h`, `xexn45` / `7yr827`, downstream `tdhav3` (Order 248), `bxupy8` (Order 290), and `ay6sxp` (Order 291), and orchestrator `63ib9r`.
- Confirmed clean partition of `2zpw22` `E-02`: `0i0zsg` owns `review_sequence`, `review_tier`, `review_rereview`, and `orchestrator_readiness`; `awmsyq` owns `production_checks`, `work_cmd`, and `artifact_adopt`; `y4spqy` creates `tests/test_readers_review_modules.py` first (`executed:y4spqy` in `0i0zsg` `- Item-Dependencies:`).
- Resolved the two cross-plan seam hazards with `7yr827` `E-04` (`restore_pre_s7_plan` write half, `PR-002`) and `bxupy8`/`ay6sxp` `E-02` (`history_block` text grammar in `count_verdict_bearing_entries` and `restore_pre_s7_plan`, `PR-001`). Note `tdhav3` `OQ-01` explicitly handles `restore_pre_s7_plan` writer regexes already removed by `7yr827` as `already gone`. Recommendation strength: very strong.

### Step S5

- Checked: three-way sort over `PR-001`..`PR-008`, `OQ-01` schema conformance (`steps/s5-questions.md` Section 3.1), remediation risk, and reversibility (`DEC-001`..`DEC-004`).
- Every finding is answered deterministically from repository code, existing test assertions, approved spec `4sd62s`, and reviewed sibling plans (`7yr827`, `6oi2nu`, `ffceq0`, `bxupy8`, `ay6sxp`); none alters scope, public CLI contracts, or release risk appetite, so zero questions require human escalation (`questions: []`). All eight findings carry `Low` remediation risk and are `FIXED` in place; `OQ-01` owner is set to `plan author` (`PR-008`). Recommendation strength: strong.

### Pass 2

- Re-read `.aw/records/plans/pending/20261109-metastore-150-0i0zsg-move-the-review-sequence-tier-rereview-and-orchestrator-read.ipd.md` top to bottom after applying `PR-001`..`PR-008`.
- Swept superseded wording across every section: removed `count_verdict_bearing_entries` from `E-01`'s moved-reader list and deferred its `history_block` call to `ay6sxp`; replaced "`restore_pre_s7_plan` still WRITES plan text and is a writer for Order 07" across `Scope`, `E-01`, `F-02`, and `## Deferred / out of scope` with `7yr827` `E-04` (`artifact_meta.restore_legacy_snapshot`); verified `mkdir -p .aw/state/t4gl15`, `D-1`..`D-3`, Mermaid `flowchart TD` terminology parity, `OQ-01` `- Owner: plan author`, and conditional `aw ipd finalize 0i0zsg` ownership.
- Verified `aw ipd lint --phase review-finalize --agent --verbose` reports `outcome: clean` with 0 errors and 0 warnings, zero em or en dashes, and `aw sanitize --agent` reports `outcome: clean` (`findings: 0`).

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R1 / R7 | `agent_workflows/review_sequence.py::count_verdict_bearing_entries` (`plan_readiness.history_block`, 0 `meta_fields`/`read_readiness` sites); `F-02` (`review_sequence` 13 sites in 5 functions: `structural_diff`, `check_S5`, `verdict_outputs`, `restore_pre_s7_plan`, `check_S7`); `bxupy8` `E-03` (Order 290) and `ay6sxp` `E-02` (Order 291) | `E-01` listed `count_verdict_bearing_entries` while omitting `structural_diff` and `check_S5`; moving `count_verdict_bearing_entries(plan_text)` onto on-disk `artifact_meta.history(id6)` before Order 290 breaks in-memory snapshot comparisons in `check_S7` and collides with `ay6sxp` `E-02` | Low | FIXED | Named all 5 `review_sequence` metadata-reader functions in `E-01` and `F-02`, left `history_block` calls for `ay6sxp` `E-02`, and added `Carrier: ay6sxp` to `## Deferred / out of scope` (`DEC-001`) |
| PR-002 | HIGH | IN-SCOPE | R2 / R7 | `agent_workflows/review_sequence.py::restore_pre_s7_plan` (lines 544, 547 `re.match(r"^-\s*(Status\|Readiness)\s*:")`); `7yr827` `E-04` (prerequisite via `executed:xexn45`); `0i0zsg` `V-01` (`rg` check for `^-` regexes) | `E-01` described `restore_pre_s7_plan` as still writing raw bullets for a future Order 07, although `7yr827` `E-04` runs before `0i0zsg` and delegates the write half to `artifact_meta.restore_legacy_snapshot` | Low | FIXED | Updated `Scope`, `E-01`, `F-02`, and `## Deferred / out of scope` (`Carrier: 7yr827, xexn45`) so `E-01` moves only the pre-pass reads while preserving `restore_legacy_snapshot` (`DEC-002`) |
| PR-003 | HIGH | IN-SCOPE | R1 / R4 | `agent_workflows/artifact_meta.py::load_legacy_artifact` (`Priority` -> `priority`, `Kind` -> `plan_role`, `Scope-Paths` -> `scope_paths`, `Item-Dependencies` -> `item_dependencies`); `tests/test_review_sequence.py::test_structural_diff` (`assert "Priority" in refused[0]`); `tests/test_review_tier.py::test_tier_facts_fixtures` and `test_tier_facts_empty_and_no_metadata` | `E-01` did not state that all 8 moved functions take `str` snapshots via `artifact_meta.read_text(text, record_type="ipd")` or record the `State` field-name, canonical bullet-casing, `TODO` `Scope-Paths`, and `id_derived` invariants | Low | FIXED | Specified `artifact_meta.read_text` across `E-01` and `READER LEDGER`, and added `## Behavior decisions` `D-2` and `D-3` (`DEC-003`) |
| PR-004 | MEDIUM | IN-SCOPE | R1 / R2 | `agent_workflows/orchestrator_readiness.py` (`_BATCH_META_RE`, `resolve_all_set_memberships`, `review_readiness`, `run_coverage`; 0 external callers of `_BATCH_META_RE`); `6oi2nu` (`source_path`, `State.id_derived`); `0i0zsg` `V-02` | `E-02` omitted the three function names, did not explicitly delete `_BATCH_META_RE` (leaving it defined fails `V-02`), and omitted `source_path`, `id_derived` skip, and untracked `read_text` fallback rules | Low | FIXED | Named all three functions and `_BATCH_META_RE` deletion in `E-02` and `F-02`, recorded `D-3`, and tightened `V-01`/`V-02` `rg` checks (`DEC-004`) |
| PR-005 | MEDIUM | IN-SCOPE | R2 | `0i0zsg` checklist preamble (`> .aw/state/t4gl15/<file>`); `.aw/.gitignore` (`state/`); `y4spqy` (`pytestmark = pytest.mark.core`) | Redirecting to `.aw/state/t4gl15/<file>` fails in a fresh isolated lane worktree without `mkdir -p .aw/state/t4gl15` | Low | FIXED | Added `mkdir -p .aw/state/t4gl15` to the baseline command and noted retaining `pytestmark = pytest.mark.core` in `tests/test_readers_review_modules.py` |
| PR-006 | MEDIUM | IN-SCOPE | R2 / S7 | `0i0zsg` `## Approval and execution gate` and `## Required tests / validation`; `.aw/system/workflows/plan-review/steps/r2-executability.md` and `steps/s7-finalize.md` | Gate lacked `never a hand git mv` and runner-vs-hand `aw ipd finalize` ownership, shared-checkout safety, narrow prerequisite stop conditions, and `aw sanitize --agent` | Low | FIXED | Added prerequisite stop conditions, shared-checkout safety, conditional runner/executor `aw ipd finalize 0i0zsg` ownership (`never a hand git mv`), and `aw sanitize --agent` |
| PR-007 | LOW | IN-SCOPE | Proofreading | `0i0zsg` preamble and `## Proposed changes (ordered, validatable)`; `.aw/system/workflows/technical-writing/technical-writing.md` Req 12(b) | Raw authoring prompt left in preamble; `## Proposed changes` had two terse lines and no Mermaid workflow diagram | Low | FIXED | Replaced preamble with conformance note, expanded both numbered steps with module/symbol names, and added a `mermaid` `flowchart TD` diagram |
| PR-008 | LOW | IN-SCOPE | S5 | `0i0zsg` `### OQ-01` (`- Status: resolved`, `- Owner: none`); `.aw/system/workflows/plan-review/steps/s5-questions.md` Section 3.1 | Resolved open question `OQ-01` carried `- Owner: none` instead of `plan author` | Low | FIXED | Updated `OQ-01` `- Owner:` from `none` to `plan author` |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| DEC-001 | How should `0i0zsg` treat `review_sequence.count_verdict_bearing_entries` at Order 150? | Leave its `plan_readiness.history_block` call in place and defer to `ay6sxp` `E-02` (Order 291), while moving all 5 bullet-metadata functions of `review_sequence` in `E-01` | Move onto `artifact_meta.history(id6)` now; add a text-history helper to `artifact_meta.py` here | `count_verdict_bearing_entries` takes in-memory `plan_text: str` (`check_S7` before/after snapshots) with 0 bullet-metadata sites (`F-02`); `bxupy8` `E-03` adds the `artifact_meta` text-history entry point at Order 290 and `ay6sxp` `E-02` moves this exact call | yes |
| DEC-002 | How should `E-01` handle `review_sequence.restore_pre_s7_plan` given `executed:xexn45`? | Move only the pre-pass `Status` and `Readiness` reads onto `artifact_meta.read_text` while keeping `7yr827` `E-04`'s `artifact_meta.restore_legacy_snapshot` write delegation intact (`Carrier: 7yr827, xexn45`) | Treat `restore_pre_s7_plan` as still doing raw `re.match` bullet writes | `0i0zsg` depends on `executed:xexn45`, which depends on `7yr827` `E-04`, and `V-01` requires zero `^-` regex matches in `agent_workflows/review_sequence.py` | yes |
| DEC-003 | How should `E-01` preserve existing test contracts when switching from `ParsedDoc.meta_fields` to `artifact_meta.read_text`? | Call `artifact_meta.read_text(text, record_type="ipd")`, map `State` attributes/fields back to canonical IPD bullet names in `structural_diff`, keep `TODO`-prefix exclusion and never-raise fallbacks in `tier_facts`, and ignore `id_derived` ids in `check_S5` (`D-2`, `D-3`) | Expose raw lowercase `REGISTRY["ipd"]` keys directly in `structural_diff`; accept `id_derived` ids as declared `Id` | `tests/test_review_sequence.py::test_structural_diff` asserts `"Priority" in refused[0]`; `tests/test_review_tier.py` pins `TODO` `Scope-Paths` and empty/headerless text; `6oi2nu` `D-3` marks cache-derived ids `id_derived` | yes |
| DEC-004 | How should `orchestrator_readiness` read tracked vs untracked plans and delete `_BATCH_META_RE` in `E-02`? | Delete `_BATCH_META_RE` (0 external callers), use `artifact_meta.query` + `source_path` (skipping `id_derived` rows) in `resolve_all_set_memberships`, and use `artifact_meta.resolve` + `read` with `read_text` fallback in `review_readiness` and `run_coverage` (`D-3`) | Leave `_BATCH_META_RE` unused; require every `review_readiness` target to live inside `.aw/records/` | Leaving `_BATCH_META_RE` fails `V-02`; `6oi2nu` scans both `.aw/records/plans` and `.agents/plans`; `read_text` fallback preserves synthetic path callers | yes |
