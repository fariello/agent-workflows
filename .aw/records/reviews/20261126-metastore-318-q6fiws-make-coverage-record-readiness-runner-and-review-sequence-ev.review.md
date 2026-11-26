# Review: 20261126-metastore-318-q6fiws-make-coverage-record-readiness-runner-and-review-sequence-ev

- Subject-Id: q6fiws
- Subject-Type: ipd
- Reviewed-At: 2026-11-26
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

- Checked: full plan `.aw/records/plans/pending/20261126-metastore-318-q6fiws-make-coverage-record-readiness-runner-and-review-sequence-ev.ipd.md` against `.aw/system/workflows/technical-writing/technical-writing.md` requirements 1 through 12, orchestrator `63ib9r` row 318 (`E-230`/`V-230`), predecessor `p109wy`, successor `e0g2gt`, later sibling `3e0vfy`, and post-patch production modules inside `.aw/system/cutover/metastore-code.cutover.patch`.

#### Changes applied during proofreading

| Location | Change | Reason |
| --- | --- | --- |
| `- Concern:` and `- Scope:` | Split long compound prose into shorter complete sentences and named exact log-format symbols (`probe_orchestrator`, `review_staleness_from_texts`, `check_S5`, `count_verdict_bearing_entries`, `run_rereview_loop`) | Requirements 2, 5, and 6 (clarity and exact scope naming) |
| `E-02` to `E-04`, `V-02` to `V-05`, `F-04` | Made log-event `date`/`model` derivation, Condition 3 `state=plan_state`, companion-log dirty check/staging, ASC history ordering, `recheck-readiness` exclusion, cache key log-mtime invalidation, list `scope_paths`, `check_S5` mirror protection, `check_S7` `_history_loader`, `run_rereview_loop` state threading, and `V-05` guard behaviors explicit | Requirements 5, 6, and 11 (verifiable requirements and technical accuracy) |

#### Unresolved ambiguity

None.

### Step T

- Q1 (Blast radius and irreversibility): Changes are confined to `.aw/system/cutover/metastore-code.cutover.patch` via a disposable scratch worktree `.aw/state/q6fiws/scratch`; no live code or public contract changes occur until attended cutover plan `cxxmyv`. Low blast radius and reversible.
- Q2 (Spec, contract, or public-interface impact): Conforms existing post-cutover code paths to already-approved spec `4sd62s` Sections 4.1 through 4.4 and N3 while keeping legacy inline fallbacks and existing public signatures intact.
- Q3 (Cross-plan / Set coupling): Member of Set `metastore` (Order 318), chained strictly after Order 317 `p109wy`, ahead of batch D `e0g2gt`, and non-overlapping with Order 321 `3e0vfy` (`plan_readiness.py` split cleanly by symbol).
- Q4 (Size and decomposition): 5 E-items (`E-01..E-05`), 3 task groups, 2 Scope-Paths (`.ipd.md` + `metastore-code.cutover.patch`), well within `IPD-Z603` bounds.
- Q5 (Security, auth, data-integrity, or safety-gate sensitivity): Touches readiness and auto-approve safety gates (`is_plan_review_approved`, `review_staleness_index`, `hold_attended_plan`, `check_S7`), requiring careful fail-closed verification across log-format and legacy paths.

AW-TIER: standard

### Step R1

- Checked: Pre-review `aw ipd lint --phase author --agent` (clean, exit 0), orchestrator `63ib9r` (`E-230`/`V-230`, row 318), predecessor `p109wy`, successor `e0g2gt` (`F-05`, `OQ-01`), later sibling `3e0vfy`, `tests/test_metastore_cutover_code_patch.py`, and post-patch code reconstructed from `metastore-docs.cutover.patch` + `metastore-code.cutover.patch` across `artifact_meta.py`, `coverage_record.py`, `orchestrator_readiness.py`, `plan_readiness.py`, `ipd_lifecycle.py`, `ipd_lint.py`, `runner_shared.py`, `review_tier.py`, `review_sequence.py`, `review_rereview.py`, `tests/test_readers_review_modules.py`, and `tests/test_readers_runner.py`.

### Step R2

- Checked: Executability and exact post-patch code behavior of every instruction in `E-01..E-05`. Found three `BLOCKER` gaps (`PR-001`, `PR-002`, `PR-003`) and one `HIGH` signature/owner-root gap (`PR-004`) where executing the plan as originally written would fail or leave silent regressions on log-format records (`coverage_checked` migration-only omission, `orchestrator_readiness` Condition 3 skipped on bare `parse`, companion-log dirty check missing, `review_staleness_index` cache key / `reviewed_text == current_text` / log-only commit gaps, `ORDER BY seq ASC` history order, `review_tier` list `scope_paths`, `check_S5` mirror corruption, `check_S7` missing `_history_loader` triggering `IPD-M107`, and `run_rereview_loop` being the sole caller of `rereview_triggers`).

### Step R3

- Checked: Safety-gate fail-closed properties on `is_plan_review_approved` (three-way rule: valid attested field, out-of-vocab fails closed without fallback, absent field inspects newest gate review event `events[-1]`, excluding `refinement` and `aw ipd recheck-readiness`), `hold_attended_plan` (headless hold on log-format `attended=required`), `coverage_record.write` (refusing to commit when companion log is already dirty so co-worker log edits are never swept in), and `check_S7` / MD-15 pre-S7 verdict guard.

### Step R4

- Checked: Testability (`E-04`/`V-04`), observable behavioral assertions (no code-pinning tests), legacy parity preservation on all optional keyword parameters, clean symbol separation from Order 321 `3e0vfy` in `plan_readiness.py`, and cumulative patch packaging (`E-05`/`V-05`).

### Step S5

- Checked: All four technical clarifications (`D-1..D-4`) were settled directly from post-patch repository code and spec `4sd62s`, with `Overall:Low` remediation risk. No human-owned open questions remain (`questions: []`).

### Pass 2

- Checked: Re-read the complete revised plan `.aw/records/plans/pending/20261126-metastore-318-q6fiws-make-coverage-record-readiness-runner-and-review-sequence-ev.ipd.md` against `PR-001..PR-005` and `technical-writing.md`. Confirmed all five findings are fixed, all `E-01..E-05` / `V-01..V-05` pairs align 1:1, the Mermaid diagram matches the checklist, no stale claims remain, and no new defects were introduced.

### Findings

| Id | Severity | Scope | Area | Evidence | Finding | Remediation risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PR-001 | blocker | in-scope | executability | `artifact_meta.py::REGISTRY` (`coverage_checked` migration-only), `artifact_meta.py::replay` (`op == "coverage"`), `coverage_record.py::write`, `orchestrator_readiness.py::review_readiness`, `ipd_lint.py::orchestrator_row_conformance` | `coverage_record.read` cannot read `coverage_checked` from `state.fields` on new `op: "coverage"` log events (it must derive `date` and `model` from the newest `op: "coverage"` log event); `orchestrator_readiness.review_readiness` calls bare `_ipd_lint.parse(text)` causing Condition 3 `orchestrator_row_conformance` to silently skip log-format orchestrators; and `coverage_record.write(..., commit=True)` must dirty-check, stage, and commit `records_root / "meta" / f"{id6}.jsonl"` alongside `rel_path` and verify `committed=True`. | Overall:Low | fixed | Updated `E-02(1)`, `E-04(1)`, `V-02`, and `F-04` (`D-1`). |
| PR-002 | blocker | in-scope | safety-gate | `plan_readiness.py::is_plan_review_approved`, `plan_readiness.py::review_staleness_from_texts`, `plan_readiness.py::review_staleness_index`, `artifact_meta.py::history` (`ORDER BY seq ASC`) | `review_staleness_index` caches solely by `(repo_root_path, rel_posix, st.st_mtime_ns)` (missing log-only `Scope-Paths` edits), `review_staleness_from_texts` returns `None` immediately when `reviewed_text == current_text`, and `git log --grep=^plan-review:` filters by plan paths only; `is_plan_review_approved` must account for `ORDER BY seq ASC` log history (`events[-1]` is newest) and exclude `refinement` and `aw ipd recheck-readiness` events from gate review provenance. | Overall:Low | fixed | Updated `E-02(2)`, `E-04(2)`, `V-02`, and `F-04` (`D-2`). |
| PR-003 | blocker | in-scope | executability | `review_tier.py::tier_facts`, `review_sequence.py::check_S5`, `review_sequence.py::verdict_outputs`, `review_sequence.py::check_S7`, `ipd_lint.py::check_readiness_attestation` (`IPD-M107`), `review_rereview.py::run_rereview_loop`, `runner_shared.py::run_review_sequence` | Five log-format defects in `E-03`: (1) `tier_facts` stringifies `list[str]` `scope_paths`, corrupting entries and breaking `names_spec`; (2) `check_S5` misses `read_mirror_id6` and prepends legacy bullets above spec-4.1a YAML review mirrors; (3) `check_S7` calls `ipd_lint.lint_text` without `_history_loader`, causing `IPD-M107` to falsely fail every log-format reviewed plan; (4) `run_rereview_loop` is the sole caller of `rereview_triggers` and must thread log state across re-review passes; and (5) `verdict_outputs` / `count_verdict_bearing_entries` must scan `ORDER BY seq ASC` log history and exclude `recheck-readiness`. | Overall:Low | fixed | Updated `E-03(1)-(4)`, `E-04(3)`, `V-03`, and `F-04` (`D-3`). |
| PR-004 | high | in-scope | interface | `runner_shared.py::hold_attended_plan`, `runner_shared.py::plan_kind_from_file`, `runner_shared.py::_read_state_for_path`, `tests/test_readers_runner.py` | Both `hold_attended_plan` and `plan_kind_from_file` take no `repo` parameter at existing call sites; `E-02(3)` must specify preserving their public signatures while deriving `owner_root` via `project_context.record_owner_root(path) or artifact_core.repo_root_of(path)` and reusing `_read_state_for_path` with safe unlogged fallback. | Overall:Low | fixed | Updated `E-02(3)` and `F-04` (`D-4`). |
| PR-005 | low | in-scope | prose | `q6fiws` `- Concern:`, `E-02` to `E-04`, `Findings`, `V-05`; `technical-writing.md` requirements 1, 2, 6, 11 | Long compound sentences, missing `F-04` static-audit anchor row, and `V-05` did not name the three observable guard behaviors of `tests/test_metastore_cutover_code_patch.py`. | Overall:Low | fixed | Tightened prose, added `F-04`, and expanded `V-05`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D-1 | How should `coverage_record.read` obtain `date`/`model` on new `op: "coverage"` log events, how should `write(..., commit=True)` handle the companion log, and how should `orchestrator_readiness.review_readiness` parse orchestrators? | Derive `date` (`observed_day` or `at[:10]`) and `model` (`actor.model`) from the newest `op == "coverage"` log event when `coverage_checked` is absent from `state.fields`; dirty-check and commit `records_root / "meta" / f"{id6}.jsonl"` alongside `rel_path`; pass `state=plan_state` to `_ipd_lint.parse` in `review_readiness`. | Modifying `artifact_meta.replay` to synthesize `coverage_checked`, or leaving Condition 3 to inline parsing. | `artifact_meta.py::REGISTRY` marks `coverage_checked` migration-only and `replay` sets only `coverage` and `coverage_fingerprint`; `ipd_lint.orchestrator_row_conformance` requires `Kind == orchestrator` in `doc.meta_fields`. | yes |
| D-2 | How should `plan_readiness` (`is_plan_review_approved`, `review_staleness_from_texts`, `review_staleness_index`) handle log history order, gate provenance, and log-only `Scope-Paths` mutations? | Inspect `events[-1]` as newest in `ORDER BY seq ASC` log history; exclude `refinement` and `aw ipd recheck-readiness` from gate review provenance; key `_STALENESS_CACHE` with companion log `(mtime_ns, size)`; add optional `reviewed_scope_paths` and `current_scope_paths` kwargs to `review_staleness_from_texts` and include companion log paths in `git log --grep=^plan-review:`. | Changing `ipd_lifecycle.frozen_region_digest` signature or disabling `_STALENESS_CACHE`. | Preserves pure 3-argument callers, closes cache staleness and `reviewed_text == current_text` short-circuit, and matches Order 321 `3e0vfy` D-2. | yes |
| D-3 | How should `review_tier`, `review_sequence`, and `review_rereview` handle list `scope_paths`, spec-4.1a review mirrors, S7 linting, and re-review loop state? | Accept both `list`/`tuple` and legacy string `scope_paths` in `tier_facts`; guard `check_S5` bullet injection with `parse_review_mirror(review_text) is None`; pass `_history_loader` alongside `state` in `check_S7`; thread `pass_start_state`, `after_r_state`, and `read_state` through `review_rereview.run_rereview_loop`. | Adding new required fields to `ReviewSequenceContext` or relaxing `IPD-M107`. | Keeps all existing signatures and `ReviewSequenceContext`'s 10 positional fields backwards-compatible while preventing `names_spec` corruption, YAML review mirror corruption, false `IPD-M107`, and missed re-review triggers. | yes |
| D-4 | How should `runner_shared.hold_attended_plan` and `plan_kind_from_file` resolve companion logs without breaking callers that pass no `repo` argument? | Preserve existing public signatures and derive `owner_root = project_context.record_owner_root(path) or artifact_core.repo_root_of(path)` before calling `_read_state_for_path`, falling back cleanly to inline text parsers on unlogged files. | Requiring a new mandatory `repo` argument on both functions. | Avoids breaking `resolve_manifest_kind`, driver calls, and `tests/test_readers_runner.py` while reading authoritative log state on log-format repos. | yes |
