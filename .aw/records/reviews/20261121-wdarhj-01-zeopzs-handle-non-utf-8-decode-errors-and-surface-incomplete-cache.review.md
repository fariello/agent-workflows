# Review findings: ipd zeopzs

- Subject-Id: zeopzs
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261124T195133Z-1320375`). The target plan `.aw/records/plans/pending/20261121-wdarhj-01-zeopzs-handle-non-utf-8-decode-errors-and-surface-incomplete-cache.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0) with two `IPD-C802` info advisories (em dashes in the runtime-demonstration reachability rule). The review read backlog item `wdarhj`, executed plans `paw8so`, `okiso1`, and `qfpnrm`, `agent_workflows/cli.py` (`_FindTypeResult`, `_find_type_records`, `find_selector_match_facts`, `_run_find_impl`, `_run_search`), `agent_workflows/artifact_meta.py` (`_load_sources`, `query`, `SUPPORTED_TYPES`), `agent_workflows/selectors.py` (`_META_TYPE_FOR_RECORD`), `agent_workflows/plans.py` (`scan`), `agent_workflows/renderers.py`, `agent_workflows/agent_schema.py`, `agent_workflows/result_types.py`, `agent_workflows/run_analytics_cli.py`, `agent_workflows/attention.py`, `docs/cli-output-contract.md`, `conftest.py`, `tests/test_find_single_read.py`, `tests/test_readers_cache_parity.py`, and `tests/test_cli_quality_gates.py`. It reproduced both defects with throwaway scripts under `/tmp/opencode/`.

### Step T

1. No; `aw find` keeps its flags, exit codes, and record kinds. The `--agent` summary gains `outcome: "partial"` / `complete: false` on a withheld record, which existing contract values already cover.
2. No; `aw find` is read-only.
3. Moderate; `5` E-items in `1` task group across `1` production module and `2` test modules.
4. Yes; `- Scope-Paths:` lists every file the plan edits.
5. Moderate; `_find_type_records` serves every `aw find` type, and the single-open guarantees in `tests/test_find_single_read.py` constrain how the fallback read may be restructured.

AW-TIER: standard

### Step R1

- Measured defect 1: in the `tests/test_readers_cache_parity.py::_build_corpus_repo` corpus with the plan overwritten by non-UTF-8 bytes, `aw find plans --agent`, `aw find plans pln001 --agent`, and `aw find --agent` raise `UnicodeDecodeError` from the plans-branch fallback `p.read_text`. `aw find specs --agent` is unaffected.
- Measured defect 2: with a valid plan and a corrupt `meta/pln001.jsonl`, `artifact_meta.query().incomplete == ['pln001']`, yet `aw find plans --agent` exits `0` and emits the `pln001` row with `"status":"pending"` under a `clean`, `complete: true` summary. F-05 said `"draft"` (`PR-005`).
- Measured the `artifacts` rows: a corrupt log stores `('pln001', None, 'meta/pln001.jsonl', 0)`, and a non-UTF-8 markdown file stores `('pln001', 'ipd', 'plans/pending/...ipd.md', 0)`. F-03 said a NULL type was why `incomplete` is unscoped; the type is only NULL for the log case, and `query(type="spec")` still returned `['pln001']` (`PR-004`).
- Measured a log-only corrupt `meta/zzz999.jsonl`: `incomplete == ['zzz999']`, `aw find --agent` reports `clean`, and `aw find zzz999 --agent` refuses with exit `2`, confirming F-04.
- Measured `chmod 0` on a plan: `aw find plans --agent` and `aw find specs --agent` raise `PermissionError` from `artifact_meta._load_sources` -> `read_bytes()`, which `test_f_unreadable_matched_plan_raises_permission_error` (IPD `qfpnrm`) pins. The plan preserved this but did not record it as a deliberate deferral (`PR-009`).
- Checked `selectors._META_TYPE_FOR_RECORD`: 7 entries; `roadmap` is in `artifact_meta.SUPPORTED_TYPES` but not mapped, so `roadmaps` queries all types. The plan said "eight `artifact_meta`-backed types" (`PR-006`).
- Checked `docs/cli-output-contract.md`: Section 12 is "Path Discovery and Resolution vs. Verification Receipts" and names no `find.*` rule; `find.id6-collision` appears in no doc (`PR-007`).

### Step R2

- Checked: E/V bijection (`5/5`), dependency order, `- Item-Dependencies: none` (correct for a lone Order 01 child with no orchestrator in Set `wdarhj`), V-item evidence demands, and the gate.
- Found E-05/V-05 demanding that `aw check all --agent` pass; on this tree it already returns `outcome findings`, exit `1`, `{"error":12,"warning":4,"info":68}` (`PR-002`).
- Found the core-tier budget unaddressed: both target modules carry `pytestmark = pytest.mark.core`, and `conftest.py::pytest_sessionfinish` enforces a 30-second wall budget (`PR-010`).
- Found the Deferred row declining the `aw search` / `aw ipd board` siblings with `Carrier-Declined` and naming a nonexistent `plans.read_status`. Both crash with `UnicodeDecodeError` (measured: `_run_search` and `plans.scan`), which makes them live bugs that must carry a release gate (`PR-008`).

### Step R3

- Checked: `aw find` is read-only. New diagnostics carry repository paths and must pass through `agent_schema.normalize_repo_path` and `redact_home_paths`, which the plan's conventions already require. `aw sanitize --agent` on the unmodified tree: `clean`, 0 findings.

### Step R4

- Found the `--agent` summary would still report `outcome: "clean"`, `complete: true` while withholding a matched record. `docs/cli-output-contract.md` "Anti-Greenwashing Invariant" forbids a positive outcome for partial work, and `render_stream` sets `complete` only from `--limit` truncation (`PR-001`).
- Found the shared fallback helper unspecified for the `research` branch: it must keep the `st.id_derived` skip and open each file once, or `test_b_find_research_single_read_non_matched` and `test_e_unparseable_research_doc_produces_no_rows` break (`PR-003`).
- Found a double-report risk: a non-UTF-8 markdown file with a filename `id6` also appears in `incomplete`, so without adding it to `handled_incomplete_ids` E-03 would report it again as log-only (`PR-004`).

### Step R7

- Checked: no other pending plan names `_find_type_records` or `_run_find_impl`. Sibling backlog `t8nqyh` (`aw specs check <id6>` false `attention.unreadable`) is a different command and does not overlap.

### Step S5

- Checked: `## Open questions`. OQ-01 (exit code and diagnostic format) and OQ-02 (`selectors._cached_states_by_path`) are resolved from repository evidence. OQ-01's resolution was amended to add the partial outcome. No blocking question remains. The new Deferred rows carry `Carrier: t5t02b` (filed at review) or a `Carrier-Declined` reason.

### Pass 2

- Re-checked the complete revised plan: front matter, `## Goal`, `E-01..E-05`, `## Project conventions discovered (Step 0)`, `## Findings` (F-01..F-07), `## Proposed changes` and both Mermaid diagrams, `## Deferred`, `## Scope check`, `## Required tests / validation`, `## Spec / documentation sync`, `## Open questions`, `V-01..V-05`, and `## Approval and execution gate`.
- Replaced the two em dashes that raised `IPD-C802`.
- `aw ipd lint --agent` returned `clean` with no diagnostics after edits.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | UNDER-SCOPE | R4 / Greenwash on withheld rows | docs/cli-output-contract.md "Anti-Greenwashing Invariant" and Section 5 `runs query` `partial` example; agent_workflows/renderers.py `render_stream` (`complete = True` unless `--limit` truncates); agent_workflows/cli.py `_run_find_impl` `outcome="clean"` | The plan withheld unreadable and incomplete records but left the `--agent` summary at `outcome: "clean"`, `complete: true`, and `--json` at `status="clean"`, which reports a partial answer as complete. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 added; E-01 tests assert `complete: false`, `outcome: "partial"`, exit `0`; E-03 renders the summary with `render_summary(..., complete=False, outcome="partial")` on the withheld path (the `run_analytics_cli.py::_emit_query_agent` pattern) and uses `CommandResult(status="partial", complete=False)`; output with no withheld record stays byte-identical; OQ-01 amended; V-03 demands the observed summary line. |
| PR-002 | MEDIUM | IN-SCOPE | R2 / Unreachable gate | `aw check all --agent` on the unmodified tree: `outcome findings`, `exit 1`, `{"error":12,"warning":4,"info":68}` | E-05 demanded that `aw check all --agent` pass, which it cannot for reasons unrelated to this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 saves a baseline to `/tmp/opencode/zeopzs-check-all-before.jsonl`; E-05 and V-05 require no new `(rule, location)` pair; Required tests notes the baseline comparison. |
| PR-003 | MEDIUM | IN-SCOPE | R4 / Single-open regression | tests/test_find_single_read.py `test_b_find_research_single_read_non_matched`, `test_e_unparseable_research_doc_produces_no_rows`; agent_workflows/cli.py research branch `if st is None or st.id_derived: continue` | Routing the research branch through a shared fallback helper without constraints could reopen files or emit rows for `id_derived` templates. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 keeps the `st.id_derived` skip for cached records, calls the helper only when `st is None`, and requires at most one read; V-02 names both tests and demands the research hunk. |
| PR-004 | MEDIUM | IN-SCOPE | R1 / Incorrect cause and double report | `artifacts` rows measured: `('pln001', None, 'meta/pln001.jsonl', 0)` and `('pln001', 'ipd', 'plans/pending/...ipd.md', 0)`; `query(type="spec").incomplete == ['pln001']` | F-03 attributed the unscoped `incomplete` to a NULL type; the type is set for markdown failures. A non-UTF-8 markdown record also in `incomplete` would be reported twice. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 rewritten with the measured rows; E-02 records one `find.unreadable-record` and adds the `id6` to `handled_incomplete_ids`. |
| PR-005 | LOW | IN-SCOPE | R1 / Observed output | `aw find plans --agent` on the Case 2 corpus: `pln001` row with `"status":"pending"`; agent_workflows/cli.py `status = disp or canon_st` | F-05 and Proposed change 1 said the fallback prints `"draft"`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05, E-01, and Proposed change 1 now state the measured `"status":"pending"` row under a `clean` summary. |
| PR-006 | LOW | IN-SCOPE | R1 / Type count | agent_workflows/selectors.py `_META_TYPE_FOR_RECORD` (7 entries); agent_workflows/artifact_meta.py `SUPPORTED_TYPES` (8, including `roadmap`) | The plan said `incomplete_set` matching applies to "the eight `artifact_meta`-backed types"; only seven trees map, and `roadmaps`, `comms`, and `other` query all types. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions and Proposed change 2 now say every type except `reviews`. |
| PR-007 | LOW | IN-SCOPE | R1 / Doc citation | docs/cli-output-contract.md Section 12 "Path Discovery and Resolution vs. Verification Receipts"; `grep -rn id6-collision docs/` (no match) | The doc-sync N/A claimed Section 12 governs `find` warning diagnostics. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec / documentation sync rewritten: Section 12 covers the stream and exit classification, the Anti-Greenwashing Invariant covers `partial`, and no doc lists `find.*` rules. |
| PR-008 | MEDIUM | IN-SCOPE | R2 / Live sibling bug declined | `aw search clean --agent` and `aw ipd board` on the Case 1 corpus raise `UnicodeDecodeError` in `cli.py::_run_search` and `plans.py::scan`; AGENTS.md "Every live bug gates the next release" | The Deferred row declined two measured crashes with `Carrier-Declined` and named `plans.read_status`, which does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Filed backlog `t5t02b` (`Work-Kind: bug`, `Blocks-Release: next`); the Deferred row now carries `Carrier: t5t02b`; Scope, F-06, and Deferred name `plans.scan`. |
| PR-009 | LOW | IN-SCOPE | R1 / Unrecorded deferral | `chmod 0` plan: `aw find plans --agent` raises `PermissionError` from `artifact_meta._load_sources`; tests/test_find_single_read.py `test_f_unreadable_matched_plan_raises_permission_error` | The plan preserved the `PermissionError` crash without recording it as deferred. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Deferred row added with a `Carrier-Declined` reason (outside `wdarhj`; reversing `qfpnrm`'s test needs its own decision); E-02 states the measured behavior. |
| PR-010 | LOW | IN-SCOPE | R2 / Core-tier budget | conftest.py `pytest_sessionfinish` (`AW_CORE_BUDGET_SECONDS`, default 30s); both target modules `pytestmark = pytest.mark.core`; 2-second slow-report threshold | New tests in the core tier could push it past its wall budget. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 requires small fixtures, in-process `_run_cli`, and each test under 2 seconds. |
| PR-011 | LOW | IN-SCOPE | Prose | `aw ipd lint --phase author --agent`: 2 `IPD-C802` | Two em dashes in the reachability rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with commas. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What outcome does `aw find` report when it withholds a record? | `complete: false`, `outcome: "partial"`, exit `0`, with the diagnostics on the summary. | Keep `clean` with warnings as `paw8so` does (rejected: `paw8so` withholds no row, and a withheld row makes the answer partial); exit `1` (rejected: `exit_contract=(0, 2)`). | docs/cli-output-contract.md "Anti-Greenwashing Invariant" and the Section 5 `partial` example at exit `0`; `agent_schema.validate_agent_record` accepts it. | Yes |
| D-2 | How is `aw check all --agent` judged when it already fails? | Compare against a baseline saved before edits; require no new diagnostic. | Require exit 0 (rejected: unreachable); drop the check (rejected: loses regression detection). | `aw check all --agent` on the unmodified tree: exit 1, 12 errors. | Yes |
| D-3 | Should the `aw search` and `aw ipd board` crashes join this plan? | No; carry them in new backlog `t5t02b` with `Blocks-Release: next`. | Widen this plan to `plans.py` and `_run_search` (rejected: outside `wdarhj`, and two more surfaces exceed the right-sizing guidance). | Measured crashes; AGENTS.md live-bug release-gate rule. | Yes |
| D-4 | Should `PermissionError` on a `chmod 0` record be handled here? | No; record it as a declined deferral. | Catch it in `_find_type_records` (rejected: it raises inside `artifact_meta.query`, out of scope, and `qfpnrm` pins it). | tests/test_find_single_read.py `test_f_unreadable_matched_plan_raises_permission_error`. | Yes |
