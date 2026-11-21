# Review findings: ipd s4utmv

- Subject-Id: s4utmv
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261121T070301Z-2497766`). The target plan `.aw/records/plans/pending/20261121-fnabjy-01-s4utmv-support-status-less-research-records-with-id-only-mirrors-in.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` findings). Inspection of backlog item `fnabjy`, spec `4sd62s` Sections 4.1 and 4.6, `agent_workflows/artifact_meta.py`, `agent_workflows/migrations/m0001_convert.py`, `agent_workflows/migrations/m0001_verify.py`, `agent_workflows/migrations/m0001_discover.py`, `agent_workflows/migrations/chain.py`, `agent_workflows/meta_cli.py`, `agent_workflows/attention.py`, `agent_workflows/research_index.py`, and `tests/test_m0001_review_conversion.py` surfaced three `HIGH`, two `MEDIUM`, and one `LOW` finding (`PR-001..PR-006`), all fixed in place. Pass 2 re-checked `Scope`, `Short-Description`, `E-01..E-05`, `Step 0`, `Findings`, `Proposed changes`, the Mermaid diagram, `Scope check`, `V-01..V-05`, and `Approval and execution gate` for full internal consistency.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `E-03` item 3, `Scope`, `Step 0`, `V-03` | Proposed allowing `allow_statusless=True` in `migrations/chain.py::_is_v2_mirror_text` by guessing from filenames lacking a non-research facet | Added optional `rel_path: Optional[str] = None` parameter to `_is_v2_mirror_text`, passed `rel_path` from `repo_has_legacy_records`, and restricted `allow_statusless=True` to `rel_path.startswith("research/")` or `.research-prompt.md` | PR-001, `steps/r1-references.md`, `steps/r4-engineering.md` |
| `E-05`, `Step 0`, `V-05` | Cited nonexistent test `test_fields_research_and_research_prompt` and omitted pre-conversion snapshot note for in-place `verify_round_trip` | Corrected to `tests/test_m0001_review_conversion.py::test_fields_research_yaml_and_nonleading_prompt_preserved` and specified snapshotting `pre_conversion_records_root` before in-place conversion | PR-002, `steps/r1-references.md` |
| `Approval and execution gate` | Unconditionally instructed `aw ipd finalize` and omitted hand-`git mv` prohibition, resolved-OQ precondition, `--scope-reason`/`--scope-ack`, shared-checkout safety, and honesty rule | Added all required execution-contract clauses including conditional runner/executor `aw ipd finalize s4utmv` ownership while preserving the Option A spec-edit note | PR-003, `steps/r2-executability.md`, `steps/s7-finalize.md` |
| `E-05`, `V-05` | Did not explicitly test `chain.repo_has_legacy_records`, spurious `status: draft` drift on status-less research, `meta_repair` restoring 1-key mirror, or non-research 1-key rejection | Added behavioral assertions for all four cases plus explicit zero-source-inspection requirement | PR-004, `steps/r4-engineering.md` |
| `Short-Description`, `E-01` item 2, `E-03` item 4 | `Short-Description` listed unmodified `attention`; `E-01`/`E-03` omitted 0/3+-key refusal details and exact `meta_cli` log-backed / repair flow | Updated `Short-Description` to name only modified components, specified 1-key/2-key/invalid-key behavior under `allow_statusless=True`, and clarified exact `meta_cli` call paths | PR-005, `steps/r1-references.md`, `steps/r4-engineering.md` |
| `E-01..E-05`, `E-04`, Mermaid diagram | Abbreviated module names, omitted exact spec `4sd62s` headings, and used unquoted Mermaid labels omitting `migrations/chain` | Qualified code citations to `path::Symbol`, added exact spec heading citations in `E-04`, and quoted Mermaid labels including `migrations/chain` | PR-006, `steps/p-proofread.md` Section 11.1, technical writing standard Requirement 12(d)-(e) |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes; updates approved spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` Sections 4.1 and 4.6 (per maintainer Option A ruling 2026-11-21) and updates the metadata-v2 mirror contract (`render_in_file_mirror`, `parse_artifact_mirror`) relied on by `60mazt`, `5qyba0`, and `cxxmyv`.
2. No; touches only metadata conversion/verification/mirror/drift modules, tests, and spec `4sd62s`, with no private-data, commit, worktree-isolation, merge, or sandbox code.
3. No; bounded single-concern change (`5` E-items in `1` task group, `8` Scope-Paths total).
4. Yes; `- Scope-Paths:` explicitly lists all 5 production files, 1 test file, spec `4sd62s`, and this IPD.
5. Yes; weakening 2-key mirror validation globally in `artifact_meta.parse_artifact_mirror` or `migrations/chain.py::_is_v2_mirror_text` would permit status-less mirrors on plans, specs, backlog items, or releases during migration and cutover.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261121-fnabjy-01-fnabjy-m0001-convert-fabricates-status-draft-for-status-l.backlog.md`, spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (Sections 4.1 and 4.6), `agent_workflows/artifact_meta.py` (`render_in_file_mirror`, `apply_in_file_mirror`, `parse_artifact_mirror`, `validate_event`, `replay`, `read_text`, `create`, `append`, `repair`), `agent_workflows/migrations/m0001_convert.py` (`build_record_log`, `rewrite_record_file`), `agent_workflows/migrations/m0001_verify.py` (`_collect_converted_records`, `_legacy_field_pairs_for_record`, `verify_round_trip`), `agent_workflows/migrations/m0001_discover.py`, `agent_workflows/migrations/chain.py` (`_is_v2_mirror_text`, `repo_has_legacy_records`), `agent_workflows/meta_cli.py` (`_parse_log_backed_mirror`, `_check_disposition_drift`, `check_meta`, `_describe_mirror_diff`, `meta_repair`), `agent_workflows/attention.py` (`_research_record`, `_reclassify_stale_research`), `agent_workflows/research_index.py` (`_scan_docs`), and `tests/test_m0001_review_conversion.py`.
- Found missing path context in `migrations/chain.py::_is_v2_mirror_text` (`PR-001`), wrong test function name (`test_fields_research_and_research_prompt` vs `test_fields_research_yaml_and_nonleading_prompt_preserved`) (`PR-002`), inaccurate `Short-Description` mentioning unmodified `attention` (`PR-005`), and abbreviated symbol citations (`PR-006`). All fixed in place.

### Step R2

- Checked: `E-*`/`V-*` bijection (`5/5`: `E-01..E-05` <-> `V-01..V-05`, `- Highest E allocated: 05`), linear dependency chain (`E-01 -> E-02 -> E-03 -> E-04 -> E-05`), `- Scope-Paths:` completeness, `- Item-Dependencies: none`, runtime reachability of `V-01..V-05` (all demand git diffs or real pytest/CLI outputs, reachable by construction), and `Approval and execution gate`.
- Found non-conforming execution contract in `Approval and execution gate` (`PR-003`: unconditional `aw ipd finalize` and missing hand-`git mv`, resolved-OQ, `--scope-reason`/`--scope-ack`, shared-checkout safety, and honesty clauses). Fixed in place.

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). Mirror rendering and parsing operate strictly on local repository records with strict line-grammar regexes and `validate_id6`, introducing no YAML parser dependencies, secrets, credentials, or outbound calls. Restricting `allow_statusless=True` in `chain._is_v2_mirror_text` to `rel_path.startswith("research/")` or `.research-prompt.md` (`PR-001`) preserves strict 2-key fail-closed validation on all other record types.

### Step R4

- Checked: correctness and data integrity (confirmed `artifact_meta.validate_event`, `replay`, `create`, `append`, `repair`, `meta_cli._check_disposition_drift`, `attention._research_record`, and `m0001_discover` already handle `status=None` on `research` cleanly; `PR-001` closes the path-scoping gap in `migrations/chain.py`; `PR-005` clarifies 1-key/2-key/error parsing and `meta_cli` flow), anti-regression and test completeness (`PR-004` adds `repo_has_legacy_records`, bidirectional `meta.status-mirror-drift`, `meta_repair`, and non-research 1-key rejection behavioral tests), right-sizing (`5` E-items, `8` Scope-Paths, cohesive single-decision delivery), and `## Spec / documentation sync` (`E-04` updates spec `4sd62s` Sections 4.1 and 4.6 per maintainer Option A approval).

### Step S5

- Checked: `## Open questions` (`None. Maintainer approved Option A on 2026-11-21`). All findings (`PR-001..PR-006`) have `Overall:Low` Remediation Risk and are settled by repository code and the maintainer's Option A ruling. Recorded `D-1` (`_is_v2_mirror_text` path-scoping via optional `rel_path`, `Reversible: yes`) in `### Decisions`. Zero blocking or human-owned questions remain.

### Pass 2

- Re-checked the complete revised plan across `Scope`, `Short-Description`, `Goal`, `E-01..E-05`, `Step 0`, `Findings`, `Proposed changes`, Mermaid diagram, `Scope check`, `Required tests / validation`, `V-01..V-05`, and `Approval and execution gate`.
- Verified `5/5` E/V bijection, `- Highest E allocated: 05`, zero unresolved questions, exact symbol/test names, and clean `aw ipd lint --phase review-finalize --agent` disposition.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R1 / R4 / Legacy-record detection | .aw/records/plans/pending/20261121-fnabjy-01-s4utmv-support-status-less-research-records-with-id-only-mirrors-in.ipd.md:55; agent_workflows/migrations/chain.py::_is_v2_mirror_text:199-217; agent_workflows/migrations/chain.py::repo_has_legacy_records:251-293 | `E-03` item 3 proposed allowing `parse_artifact_mirror(..., allow_statusless=True)` in `migrations/chain.py::_is_v2_mirror_text` using a heuristic ("research `.md` file lacking a non-research type facet"). `_is_v2_mirror_text(text, filename)` receives no directory path, and matching any `.md` lacking a non-research facet would wrongly accept 1-key mirrors on legacy un-faceted non-research `.md` files. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-03` item 3, `Scope`, `Step 0`, and `V-03` to add an optional `rel_path: Optional[str] = None` keyword parameter to `_is_v2_mirror_text`, pass `rel_path=(cur_path / fname).relative_to(root_dir).as_posix()` from `repo_has_legacy_records`, and allow `allow_statusless=True` only when `rel_path.startswith("research/")` or `filename.endswith(".research-prompt.md")` (`D-1`). Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R1 / Test citation accuracy | .aw/records/plans/pending/20261121-fnabjy-01-s4utmv-support-status-less-research-records-with-id-only-mirrors-in.ipd.md:66,77; tests/test_m0001_review_conversion.py::test_fields_research_yaml_and_nonleading_prompt_preserved:243-369 | `E-05` named `test_fields_research_and_research_prompt`, which does not exist in `tests/test_m0001_review_conversion.py`; the actual test containing `rs5002` and `assert st2.status == "draft"` (line 361) is `test_fields_research_yaml_and_nonleading_prompt_preserved`, which converts `rec` in place so calling `m0001_verify.verify_round_trip` requires snapshotting `pre_conversion_records_root` beforehand. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected the test name to `tests/test_m0001_review_conversion.py::test_fields_research_yaml_and_nonleading_prompt_preserved` in `E-05`, `Step 0`, and `V-05`, and noted snapshotting `pre_conversion_records_root` before in-place conversion for `verify_round_trip`. Recommendation strength: very strong. |
| PR-003 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261121-fnabjy-01-s4utmv-support-status-less-research-records-with-id-only-mirrors-in.ipd.md:162-167; .aw/system/workflows/plan-review/steps/r2-executability.md:57-60; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | `Approval and execution gate` unconditionally instructed running `aw ipd finalize` and omitted the explicit hand-`git mv` prohibition, resolved-open-questions precondition, `--scope-reason`/`--scope-ack` scope-fence variance rule, shared-checkout safety rule, and hard-MUST paste-actual-runner-output honesty rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` with all required execution-contract clauses and conditional runner/executor `aw ipd finalize s4utmv` ownership while preserving the Option A spec-edit note. Recommendation strength: very strong. |
| PR-004 | MEDIUM | UNDER-SCOPE | R4 / Testing coverage | .aw/records/plans/pending/20261121-fnabjy-01-s4utmv-support-status-less-research-records-with-id-only-mirrors-in.ipd.md:52-59,66-69,157-160 | `E-05` did not explicitly assert `chain.repo_has_legacy_records` (`False` on migrated `id`-only research, `True` on non-research 1-key mirror), reverse `meta.status-mirror-drift` (status-less research with spurious `status: draft`), `aw meta repair <id6> --apply` restoring the 1-key mirror, or zero source-code inspection checks. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Extended `E-05` and `V-05` to require behavioral assertions for `repo_has_legacy_records`, bidirectional `meta.status-mirror-drift`, `meta_repair` restoring 1-key mirrors, non-research 1-key rejection, and zero source-code inspection checks. Recommendation strength: strong. |
| PR-005 | MEDIUM | IN-SCOPE | R1 / R4 / Precision & mirror flow | .aw/records/plans/pending/20261121-fnabjy-01-s4utmv-support-status-less-research-records-with-id-only-mirrors-in.ipd.md:10,41,56; agent_workflows/meta_cli.py::check_meta:972-990; agent_workflows/meta_cli.py::_describe_mirror_diff:1424-1431 | `Short-Description` listed `attention` even though `agent_workflows/attention.py` is unmodified; `E-01` item 2 did not explicitly specify that `allow_statusless=True` accepts both 1-key and 2-key mirrors while rejecting 0 or 3+ keys; and `E-03` item 4 did not clarify how `check_meta`, `_describe_mirror_diff`, and `meta_repair` flow through `_parse_log_backed_mirror` and `apply_in_file_mirror`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `Short-Description` to name only modified components (`m0001_convert`, `artifact_meta`, `m0001_verify`, `migrations/chain`, `meta_cli`, spec `4sd62s`), specified 1-key/2-key/invalid-key rules in `E-01`, and clarified exact `meta_cli` call paths in `E-03`. Recommendation strength: strong. |
| PR-006 | LOW | IN-SCOPE | Proofreading / R1 / Technical writing standard | .aw/records/plans/pending/20261121-fnabjy-01-s4utmv-support-status-less-research-records-with-id-only-mirrors-in.ipd.md:39-68,94-101; .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:375,1295 | `E-01..E-05` used abbreviated module references instead of `path::Symbol`, `E-04` omitted the exact spec `4sd62s` section headings, and the Mermaid diagram had unquoted labels with colons/commas and omitted `migrations/chain`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Qualified symbol citations to `path::Symbol`, cited exact spec headings in `E-04` and `V-04`, and updated the Mermaid diagram with quoted labels including `migrations/chain`. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `agent_workflows/migrations/chain.py::_is_v2_mirror_text` decide when to permit a 1-key `id`-only mirror for status-less `research` records? | Add an optional `rel_path: Optional[str] = None` keyword argument to `_is_v2_mirror_text`, pass `rel_path=(cur_path / fname).relative_to(root_dir).as_posix()` from `repo_has_legacy_records`, and enable `parse_artifact_mirror(text, allow_statusless=True)` only when `(rel_path is not None and rel_path.startswith("research/"))` or `filename.endswith(".research-prompt.md")`. | Match any `.md` file lacking a non-research type facet (rejected: falsely accepts 1-key mirrors on legacy un-faceted non-research `.md` files); match `.research-prompt.md` only (rejected: misses migrated status-less legacy research notes such as `20260708-survey-notes.md` under `research/`). | `agent_workflows/migrations/chain.py::_is_v2_mirror_text:199`, `agent_workflows/migrations/chain.py::repo_has_legacy_records:251`, backlog `fnabjy` | yes |
