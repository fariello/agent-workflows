# Review findings: ipd vvxbbl

- Subject-Id: vvxbbl
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261121T070301Z-2497766`). The target plan `.aw/records/plans/pending/20261121-7mmhlp-01-vvxbbl-return-migrated-legacy-research-records-lacking-a-kind-facet.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` findings). Inspection of backlog item `7mmhlp`, `agent_workflows/cli.py` (`_find_type_records`, `_resolve_selectors_with_kinds`), `agent_workflows/selectors.py` (`_iter_paths`), `tests/test_find_filters.py`, and `tests/test_find_single_read.py` (`test_e_unparseable_research_doc_produces_no_rows`) surfaced one `HIGH`, two `MEDIUM`, and one `LOW` finding (`PR-001..PR-004`), all fixed in place. Pass 2 re-checked `Scope`, `Goal`, `E-01..E-02`, `Step 0`, `Findings`, `Proposed changes`, the Mermaid diagram, `Deferred / out of scope`, `Scope check`, `V-01..V-02`, and `Approval and execution gate` for full internal consistency.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Approval and execution gate` | Unconditionally instructed `aw ipd finalize` and omitted hand-`git mv` prohibition, resolved-OQ precondition, `--scope-reason`/`--scope-ack`, shared-checkout safety, and honesty rule | Added all required execution-contract clauses including conditional runner/executor `aw ipd finalize vvxbbl` ownership | PR-001, `steps/r2-executability.md`, `steps/s7-finalize.md` |
| `E-02`, `Step 0`, `V-02` | Did not isolate the test fixture from `TestFindFilters.setUp`'s pre-existing `res001` record, omitted the concrete `meta/ab12cd.jsonl` checkpoint shape, and omitted zero-source-inspection constraint | Specified an isolated temporary repository, concrete `checkpoint` event shape independent of `s4utmv`, `--set ab12cd` filter check, and zero-source-inspection constraint | PR-002, `steps/r1-references.md`, `steps/r4-engineering.md` |
| `E-01`, `Scope`, `Step 0`, `Scope check`, `V-01` | Relied on `st.legacy_raw_status or ""` without `st.status` fallback and did not explicitly pin `test_e_unparseable_research_doc_produces_no_rows` | Added `st.status` fallback when `st.legacy_raw_status is None` and explicitly cited `tests/test_find_single_read.py::test_e_unparseable_research_doc_produces_no_rows` as a preserved anti-regression invariant | PR-003, `steps/r4-engineering.md` |
| `Step 0`, `E-01`, `Deferred / out of scope`, `Proposed changes` | Misattributed `_resolve_selectors_with_kinds` to `selectors` instead of `agent_workflows/cli.py`, used abbreviated symbol names, lacked `- Carrier-Declined:` on declined deferred alternative, and lacked a Mermaid flowchart | Corrected citation to `agent_workflows/cli.py::_resolve_selectors_with_kinds`, qualified symbol citations to `path::Symbol`, added `- Carrier-Declined:`, and added a Mermaid flowchart per Requirement 12(b) | PR-004, `steps/r1-references.md`, `steps/p-proofread.md` Section 11.1, technical writing standard Requirement 12(b) |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes; changes which `research` records `aw find` emits when `research_contract.parse_name` returns `None`, relied upon by `60mazt` AC-42(4)/(5) parity.
2. No; touches only the `research` loop in `agent_workflows/cli.py::_find_type_records` and `tests/test_find_filters.py`, with no private-data, commit, worktree-isolation, merge, or sandbox code.
3. No; very small and focused (`2` E-items in `1` task group across `1` production file and `1` test file).
4. Yes; `- Scope-Paths:` explicitly lists `agent_workflows/cli.py`, `tests/test_find_filters.py`, and this IPD.
5. Yes; dropping the `st is None or st.id_derived` guard or dereferencing `parsed` when `None` would crash `aw find` or break `tests/test_find_single_read.py::test_e_unparseable_research_doc_produces_no_rows` and pre-migration parity.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261121-7mmhlp-01-7mmhlp-aw-find-drops-migrated-legacy-research-records-who.backlog.md`, `agent_workflows/cli.py` (`_find_type_records`, `_resolve_selectors_with_kinds`), `agent_workflows/selectors.py` (`_iter_paths`), `tests/test_find_filters.py` (`TestFindFilters.setUp`), and `tests/test_find_single_read.py` (`test_e_unparseable_research_doc_produces_no_rows`).
- Found misattributed module in `Step 0` (`selectors._resolve_selectors_with_kinds` actually lives in `agent_workflows/cli.py`) (`PR-004`), fixture collision risk with `TestFindFilters.setUp`'s `res001` (`PR-002`), and abbreviated symbol citations (`PR-004`). All fixed in place.

### Step R2

- Checked: `E-*`/`V-*` bijection (`2/2`: `E-01..E-02` <-> `V-01..V-02`, `- Highest E allocated: 02`), dependency chain (`E-01 -> E-02`), `- Scope-Paths:` completeness, `- Item-Dependencies: none` (confirmed independent of `s4utmv`), runtime reachability of `V-01..V-02` (both demand git diffs or real pytest/CLI outputs, reachable by construction), and `Approval and execution gate`.
- Found non-conforming execution contract in `Approval and execution gate` (`PR-001`: unconditional `aw ipd finalize`, missing hand-`git mv` prohibition, resolved-OQ precondition, `--scope-reason`/`--scope-ack`, shared-checkout safety, and honesty clauses). Fixed in place.

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). `_find_type_records` is read-only over local `artifact_meta` cache rows and file paths; preserving `st is None or st.id_derived` avoids exposing unindexed/unmigrated prose files and introduces no new trust boundaries, writes, or leaks.

### Step R4

- Checked: correctness and data integrity (`PR-003` adds `st.status` fallback when `st.legacy_raw_status is None` and preserves `st is None or st.id_derived` guard), anti-regression (`tests/test_find_single_read.py::test_e_unparseable_research_doc_produces_no_rows` explicitly pinned; `PR-002` isolates `E-02` from `TestFindFilters.setUp`'s `res001` and specifies concrete checkpoint fixture shape independent of `s4utmv`), right-sizing (`2` E-items, `3` Scope-Paths, cohesive single bugfix), and `## Spec / documentation sync` (`N/A` verified truthful: aligns `aw find research` with spec `4sd62s` C1/C5).

### Step S5

- Checked: `## Open questions` (`None.`). Every finding (`PR-001..PR-004`) has `Overall:Low` Remediation Risk. Recorded `D-1` (honoring `artifact_meta.State` in `cli._find_type_records` rather than fabricating synthetic kind facets in `m0001_renames`, settled by spec `4sd62s` C1/4.2a, `Reversible: yes`) in `### Decisions`. Zero blocking or human-owned questions remain.

### Pass 2

- Re-checked the complete revised plan across `Scope`, `Goal`, `E-01..E-02`, `Step 0`, `Findings`, `Proposed changes`, Mermaid diagram, `Deferred / out of scope`, `Scope check`, `Required tests / validation`, `V-01..V-02`, and `Approval and execution gate`.
- Verified `2/2` E/V bijection, `- Highest E allocated: 02`, zero unresolved questions, and clean `aw ipd lint --phase review-finalize --agent` disposition.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261121-7mmhlp-01-vvxbbl-return-migrated-legacy-research-records-lacking-a-kind-facet.ipd.md:107-112; .aw/system/workflows/plan-review/steps/r2-executability.md:57-60; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | `Approval and execution gate` unconditionally instructed running `aw ipd finalize` and omitted the explicit hand-`git mv` prohibition, resolved-open-questions precondition, `--scope-reason`/`--scope-ack` scope-fence variance rule, shared-checkout safety rule, and hard-MUST paste-actual-runner-output honesty rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` with all required execution-contract clauses and conditional runner/executor `aw ipd finalize vvxbbl` ownership. Recommendation strength: very strong. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / R4 / Test fixture isolation | .aw/records/plans/pending/20261121-7mmhlp-01-vvxbbl-return-migrated-legacy-research-records-lacking-a-kind-facet.ipd.md:46-49; tests/test_find_filters.py::TestFindFilters.setUp:104-132 | `TestFindFilters.setUp` already creates `res001` in `self.repo_root`, so reusing `self.repo_root` would yield `total == 2` instead of `total == 1` on `aw find research --agent`. `E-02` also omitted the concrete `meta/ab12cd.jsonl` checkpoint event shape (ensuring independence from `s4utmv`) and the zero-source-inspection constraint. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-02`, `Step 0`, and `V-02` to require an isolated temporary repository, specify the concrete `checkpoint` event shape independent of `s4utmv`, check `--set ab12cd`, and prohibit source-code inspection checks. Recommendation strength: strong. |
| PR-003 | MEDIUM | IN-SCOPE | R1 / R4 / Status fallback and anti-regression | .aw/records/plans/pending/20261121-7mmhlp-01-vvxbbl-return-migrated-legacy-research-records-lacking-a-kind-facet.ipd.md:38-44; agent_workflows/cli.py::_find_type_records:15767; tests/test_find_single_read.py::test_e_unparseable_research_doc_produces_no_rows:371-390 | `agent_workflows/cli.py:15767` reads `raw_st = st.legacy_raw_status or ""` without falling back to `st.status`, and the plan did not explicitly pin `tests/test_find_single_read.py::test_e_unparseable_research_doc_produces_no_rows` as an anti-regression invariant. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `st.status` fallback when `st.legacy_raw_status is None` in `E-01` and explicitly documented `test_e_unparseable_research_doc_produces_no_rows` as a preserved invariant in `E-01`, `Step 0`, `Scope check`, and `V-02`. Recommendation strength: strong. |
| PR-004 | LOW | IN-SCOPE | Proofreading / R1 / Technical writing standard | .aw/records/plans/pending/20261121-7mmhlp-01-vvxbbl-return-migrated-legacy-research-records-lacking-a-kind-facet.ipd.md:53,68-71; agent_workflows/cli.py:15723 | `Step 0` misattributed `_resolve_selectors_with_kinds` to `selectors` (it lives in `agent_workflows/cli.py`), citations used abbreviated module names, `Deferred / out of scope` lacked `- Carrier-Declined:`, and `Proposed changes` lacked a Mermaid flowchart for the branched lookup flow (Requirement 12(b)). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected citation to `agent_workflows/cli.py::_resolve_selectors_with_kinds`, qualified symbol citations to `path::Symbol`, added `- Carrier-Declined:`, and added a Mermaid flowchart in `Proposed changes`. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should migrated legacy research files lacking a `.<kind>.md` facet be surfaced by falling back to `artifact_meta.State` in `cli._find_type_records`, or by fabricating a synthetic kind facet in `m0001_renames`? | Fall back to `artifact_meta.State` in `agent_workflows/cli.py::_find_type_records` when `st is not None and not st.id_derived` and `st.id6` is non-empty, leaving `m0001_renames` unchanged. | Fabricate a synthetic `.<kind>.md` facet in `m0001_renames` (rejected: violates spec `4sd62s` 4.2a legacy-import preservation by inventing ungrounded metadata when `artifact_meta` is already the C1/C5 authority). | Spec `4sd62s` C1, C5, 4.2a; backlog `7mmhlp`; `agent_workflows/cli.py::_find_type_records:15757` | yes |
