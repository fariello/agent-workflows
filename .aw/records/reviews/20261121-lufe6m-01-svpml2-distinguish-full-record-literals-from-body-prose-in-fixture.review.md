# Review findings: ipd svpml2

- Subject-Id: svpml2
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261124T195133Z-1320375`). The target plan `.aw/records/plans/pending/20261121-lufe6m-01-svpml2-distinguish-full-record-literals-from-body-prose-in-fixture.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0) with two `IPD-C802` info advisories (em dashes in the validation-state rule paragraph). The review read backlog item `lufe6m`, executed plans `lf0fe4`, `59aiyh`, `y3uowx`, and `j2xjtt`, sibling plans `kbh055` and `osq7nu`, `tools/fixture_codemod.py`, `tests/test_fixture_codemod.py`, `tests/test_fixture_codemod_slow.py`, `tests/slow_allowlist.txt`, `tests/fixtures/fixture_codemod/`, `tests/test_attention.py`, `tests/test_readers_check_engine.py`, `tests/test_review_rereview.py`, `tests/test_selector_two_dialect_readers.py`, `conftest.py`, `Makefile`, and the carrier rule in `agent_workflows/check_engine.py`.

### Step T

1. No; the change is internal to a standalone maintenance tool (`tools/fixture_codemod.py`) and adds no CLI flag, reason code, or public API.
2. No; the tool's only write path is `--apply`, which already proves pytest outcome equivalence per module and reverts non-equivalent sites.
3. Moderate; `5` E-items in `3` task groups across `1` tool, `1` fixture, `3` test files, and the slow allowlist.
4. Yes; `- Scope-Paths:` lists every file the plan edits.
5. Moderate; the new heuristic decides classification for every `body=` site in `tests/`, so an over-broad rule would silently reclassify sites in modules the plan never inspects.

AW-TIER: standard

### Step R1

- Checked: every cited symbol exists with the stated role: `_is_body_or_oq_kwarg` (signature `(site_node, parents)`), `_plan_site` step 4 (`_is_body_or_oq_kwarg(node, parents) or _is_body_prose_text(template)`), `_extract_template`, `_is_body_prose_text`, `_infer_type_from_template`, `_collect_record_builder_var_names` (`ast.Assign` only), `_YAML_RESEARCH_SITE_RE`, `_HEADING_TO_RECORD_TYPE`, `_PLACEHOLDER_RE`, `_BULLET_LINE_RE`, `analyze_module`, `apply_rewrites_to_source`, and `main`.
- Measured: a whole-tree dry run (`817` modules, `1394` sites, `rewrites=30`, `body prose=154`) and the same run with `_is_body_or_oq_kwarg` forced to `False`. Exactly three sites change, all in `tests/test_attention.py` (lines 2678, 2688, 2973), giving `rewrites=33` and `body prose=151`. This confirms plan F-03 and shows `_is_body_prose_text` alone already keeps every other `body=` site as body prose.
- Measured: the `body=`/`open_questions=` census is 3 `_mk_plan` sites, 5 `tests/test_readers_check_engine.py` sites (2 `## Open questions`, 3 `## Notes`; no `## Workflow history`), 1 `open_questions=` site in `tests/test_review_rereview.py`, and 1 `# Quoting Report` site in `tests/test_selector_two_dialect_readers.py`. The plan said 6 readers sites including `## Workflow history` and omitted the rereview site (`PR-002`).
- Found the "76 existing `hand` sites" claim unsupported: the readers module has 10 sites, 1 `unsupported-shape` (`PR-002`).
- Found that importing `tools/fixture_codemod.py` via `spec_from_file_location` without `sys.modules` registration fails with `AttributeError: 'NoneType' object has no attribute '__dict__'` (dataclass construction), which E-02's in-process tests would hit (`PR-004`).

### Step R2

- Checked: E/V bijection (`5/5`), dependency order, `- Item-Dependencies: none` (correct for a lone Order 01 child), V-item evidence demands, and the gate.
- Found the Deferred row carrying both `Carrier: 59aiyh` and `Carrier-Evidence`; `59aiyh` is in `executed/`, so the `Carrier` reads as finished and fails the carrier rule. The row now carries only `Carrier-Evidence` (`PR-001`).
- Found no pre-change baseline, so E-04's "only the expected sites changed" could not be shown, and `aw check all --agent` already exits 1 on this tree, so E-05's "zero failures" could not pass (`PR-005`, `PR-006`).
- Found `make typecheck` covers only `agent_workflows/` (`PR-007`).

### Step R3

- Checked: no security surface. The tool reads test sources and, under `--apply`, runs pytest on the repository's own test modules; the change only moves which sites reach the existing rewrite path, all of which stay inside the per-module equivalence proof.

### Step R4

- Checked: the proposed `_looks_like_full_record_literal` rules against each census site and against the existing step-4 `_is_body_prose_text` check, which still runs on every template.
- Found the heading-less two-bullet rule would count `- Status: open` plus `- Finding: F-001` (a real shape in `tests/test_readers_check_engine.py`) as two metadata bullets; the open-question key set now derives from `agent_workflows/ipd_schema.py::OQ_FIELDS` (`PR-003`).
- Found the `AnnAssign` test as drafted (a call producing `sites=0`) passes before the fix unless the call carries an F-01 literal (`PR-008`).
- Found heading-less review literals need `- Subject-Id:` plus `- Subject-Type:` or `- Verdict:` to infer a type (`PR-008`), and test module names must avoid the legacy-subject globs and markers (`PR-009`).
- Found the flowchart showed `_is_body_prose_text` only on the `body=` branch and attributed the whole step-4 decision to `_is_body_or_oq_kwarg` (`PR-010`).

### Step R7

- Checked: sibling plans `kbh055` (Set `b1j6bl`, `to-review`) and `osq7nu` (Set `e0wwtc`, `reviewed`) edit `tools/fixture_codemod.py` in `_plan_site` field mapping and H1 title handling; neither touches `_is_body_or_oq_kwarg`, `_collect_record_builder_var_names`, or step 4. Overlap is limited to the same file, which the runner's isolated worktrees and merge gate handle.

### Step S5

- Checked: `## Open questions`. OQ-01 (remove or restrict `_is_body_or_oq_kwarg`) is resolved from repository evidence. No blocking question remains.

### Pass 2

- Re-checked the complete revised plan: front matter, `## Goal`, `E-01..E-05`, `## Project conventions discovered (Step 0)`, `## Findings`, `## Proposed changes` and both Mermaid diagrams, `## Deferred`, `## Scope check`, `## Required tests / validation`, `## Spec / documentation sync`, `## Open questions`, `V-01..V-05`, and `## Approval and execution gate`.
- Replaced the two em dashes that raised `IPD-C802`.
- `aw ipd lint --phase author --agent` returned `clean` with no diagnostics after edits.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | R2 / Carrier rule | agent_workflows/check_engine.py `evaluate_carrier_obligation`; .aw/records/plans/executed/20261102-metastore-10-59aiyh-move-test-data-to-one-shared-record-builder-over-artifact-me.ipd.md (`- Status: executed`) | The Deferred row named `Carrier: 59aiyh` beside `Carrier-Evidence`; `59aiyh` is executed, so the `Carrier` reads as finished. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The row keeps only `Carrier-Evidence` for the executed plan and states why the readers module needs no further work. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / Census accuracy | `python3 tools/fixture_codemod.py --dry-run --format json tests/test_readers_check_engine.py` (10 sites, 1 `unsupported-shape`, 7 `body prose`); tests/test_review_rereview.py:538 | The plan claimed 76 `hand` sites in the readers module, 6 readers `body=` sites including `## Workflow history`, and omitted the `open_questions=` site. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope OUT clause, F-02, F-04, and the Deferred row restated from the measured census. |
| PR-003 | HIGH | IN-SCOPE | R4 / Heuristic over-trigger | tests/test_readers_check_engine.py:1092 (`- Blocking`, `- Status`, `- Owner`, `- Finding`); agent_workflows/ipd_schema.py `OQ_FIELDS` | The two-metadata-bullet rule excluded only four open-question keys, so `- Status: open` plus `- Finding:` would count as a record. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 derives the excluded keys from `OQ_FIELDS` minus `status` plus `resolution`; E-02 (c) adds the fragment as a kept-prose case. |
| PR-004 | HIGH | IN-SCOPE | R1 / In-process import | `spec_from_file_location` load without `sys.modules` registration: `AttributeError: 'NoneType' object has no attribute '__dict__'`; no tools/__init__.py | E-02's in-process tests would fail at import because the tool's dataclasses need the module registered. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names the loading recipe and the observed failure; Step 0 records that `tools/` is not a package. |
| PR-005 | HIGH | UNDER-SCOPE | R2 / No regression baseline | Whole-tree dry run, baseline vs. forced-`False`: only 3 sites change | Nothing showed that the new heuristic leaves every other site in `tests/` unchanged. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 captures `.aw/state/svpml2/dryrun-before.json` first; E-04 diffs it site by site and allows only the three `tests/test_attention.py` sites to change; V-01 and V-04 demand the evidence. |
| PR-006 | MEDIUM | IN-SCOPE | R2 / Unreachable gate | `aw check all --agent` on the unmodified tree: `outcome findings`, `exit 1`, 12 errors | E-05 demanded zero failures from a check that already fails for unrelated reasons. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 captures `.aw/state/svpml2/check-before.jsonl`; E-05 and V-05 require no new `{location, rule}` diagnostic. |
| PR-007 | LOW | IN-SCOPE | R2 / Typecheck coverage | Makefile `typecheck: python3 -m mypy agent_workflows`; `python3 -m mypy tools/fixture_codemod.py` (Success) | `make typecheck` does not cover the edited tool. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05, V-05, and Required tests add `python3 -m mypy tools/fixture_codemod.py`. |
| PR-008 | MEDIUM | IN-SCOPE | R4 / Tests that cannot fail | tools/fixture_codemod.py `_collect_candidate_sites` (skips RecordBuilder calls), `_infer_type_from_template` (review needs `Subject-Id` plus `Subject-Type` or `Verdict`) | The `AnnAssign` case passes before the fix unless its call carries an F-01 literal, and the heading-less review case named only `- Subject-Id:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 (d) requires an F-01 literal inside the `AnnAssign`-bound call; E-02 (a) names the review field pair. |
| PR-009 | LOW | IN-SCOPE | R4 / Legacy-subject masking | tools/fixture_codemod.py `_LEGACY_SUBJECT_MODULE_GLOBS`, `_LEGACY_SUBJECT_FUNC_MARKERS`; `_plan_site` step 1 | A temporary test module or function named to match a legacy glob or marker is refused before step 4, hiding the behavior under test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires names that match neither list. |
| PR-010 | LOW | IN-SCOPE | R4 / Diagram accuracy | tools/fixture_codemod.py `_plan_site` step 4 | The flowchart applied `_is_body_prose_text` only to `body=` and attributed the whole decision to `_is_body_or_oq_kwarg`; E-03 also lacked the allowlist line format and the rewritten-module `cwd`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Flowchart now routes non-keyword sites to the same check and labels the step-4 decision; E-03 names the `<node id><TAB><reason>` format, `cwd=str(support.REPO_ROOT)`, and the proof location. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How does the executor show the heuristic changes nothing else? | A whole-tree dry-run JSON before E-01, diffed site by site after E-01, allowing only the three known `tests/test_attention.py` sites to change. | Rely on the new unit tests alone (rejected: they cover chosen shapes, not the 1394 real sites). | Review-time simulation: forcing the keyword check off changes exactly those three sites. | Yes |
| D-2 | How is `aw check all --agent` judged when it already fails? | Compare against a baseline captured before edits; require no new diagnostic. | Require exit 0 (rejected: unreachable for unrelated reasons); drop the check (rejected: loses regression detection). | `aw check all --agent` on the unmodified tree: exit 1, 12 errors. | Yes |
