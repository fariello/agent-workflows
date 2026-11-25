# Review findings: ipd fkvrc7

- Subject-Id: fkvrc7
- Subject-Type: ipd
- Reviewed-At: 2026-11-25
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261125T044745Z-2905371`). The target plan `.aw/records/plans/pending/20261124-metastore-303-fkvrc7-replace-surviving-specs-and-backlog-front-matter-regexes-via.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` findings). The review read spec `4sd62s` (C5, C10a, AC-1), backlog items `ebbfmn` and `vl7ybn`, `Set: metastore` orchestrator `63ib9r` and sibling plans `9o83cr`, `wgn3bl`, `t3t7za`, `75jciz`, and superseded `rgva3w`, plus all target modules (`artifact_meta.py`, `specs.py`, `backlog.py`, `spec_citations.py`, `migrations/chain.py`) and affected tests (`tests/test_backlog_metadata_duplicate_and_gate_summary.py`, `tests/test_specs_metadata_duplicate_bullet.py`). It found three `HIGH` and four `MEDIUM` findings (`PR-001..PR-007`), all `Overall:Low` remediation risk and all fixed in place. No production code or test code was modified.

### Step T

1. Yes; the plan adds a new public library helper (`list_metadata_bullets`) to `agent_workflows/artifact_meta.py`, removes private regex globals (`specs._SPEC_ID_RE`, `specs._TOP_KEY_RE`, `specs._SPEC_ID_BULLET_RE`, `backlog._TOP_KEY_RE`), and satisfies the `executed:fkvrc7` prerequisite of `9o83cr` `E-14` in `Set: metastore`.
2. No; it touches no private-data, commit-lock, worktree-isolation, merge, or sandbox guard modules.
3. Moderate; 4 E-items in 3 task groups across 4 production modules and 2 test modules, coordinated inside `Set: metastore`.
4. Yes; `- Scope-Paths:` declared 5 production files and 2 test files, and static inspection found two bad entries: `tests/test_specs.py` does not exist and `agent_workflows/migrations/chain.py` has zero `^-` regexes.
5. Yes; mistakes in metadata-block boundary rules break `backlog.metadata-bullet-repeated` (`test_sub_bullet_boundary_deliberate_non_finding`), `spec.metadata-bullet-repeated`, `specs.run_migrate`, or the `_review_attestation_refusal` / `_deferred_ids_refusal` transition gates.

AW-TIER: complex

### Step R1

- Checked: every file, symbol, regex literal, and test path referenced by the plan: `agent_workflows/specs.py` (`_metadata_end` lines 68-71, `_SPEC_ID_RE` line 158, `_TOP_KEY_RE` line 159, `validate_spec` lines 291-310, `run_migrate` lines 849-906, `run_note` line 966, `_existing_spec_ids` line 994, `_SPEC_ID_BULLET_RE` line 1289, `_review_attestation_refusal` line 1311, `_deferred_ids_refusal` line 1365), `agent_workflows/backlog.py` (`_TOP_KEY_RE` line 104, `validate_item` lines 413-431), `agent_workflows/spec_citations.py::stale_spec_anchors` (line 214), `agent_workflows/artifact_meta.py` (`parse_metadata_block` lines 2698-2737, `read_loose_id` line 5273), `agent_workflows/migrations/chain.py` (zero `^-` regexes across all 387 lines), `agent_workflows/runner_shared.py::_region_bullet_keys` (line 5755), `agent_workflows/plans_refs.py::_check_order_lines` (line 96), and `tests/`.
- Found: `tests/test_specs.py` does not exist (`PR-001`), `migrations/chain.py` has zero `^-` regexes (`PR-003`), and `vl7ybn` also names two non-regex callers outside this plan's scope (`PR-005`). All fixed in place.

### Step R2

- Checked: E/V bijection (`4/4`: `E-01..E-04` to `V-01..V-04`, `- Highest E allocated: 4`), dependency chain (`E-01 -> E-02 -> E-03 -> E-04`), `- Item-Dependencies:` (all 5 split parts `0xsx2n`, `e8420v`, `k6jd6l`, `q6epwc`, `snin8q` are `executed`), concrete `V-*` evidence demands, runtime-demonstration reachability (all `V-*` demand `pytest`, `mypy`, `rg`, or `aw sanitize --agent` output, reachable by construction), and `## Approval and execution gate`.
- Found: nonexistent `tests/test_specs.py` in `- Scope-Paths:`, `E-03`, and `V-03` (`PR-001`); missing `@pytest.mark.core`, missing bare `python3 -m pytest`, and bare `aw sanitize` (`PR-006`); and incomplete `## Approval and execution gate` (`PR-007`). All fixed in place.

### Step R3

- Checked: the plan moves pure read-only metadata bullet scanning into `artifact_meta.py` with no new I/O, shell calls, network calls, secrets, or privilege bypasses. Requiring `\r\n` normalization and `\n`-only splitting (never `str.splitlines()`) prevents bare `\r` / U+2028 line-splitting from forging metadata bullets, matching `artifact_meta._parse_bullet_metadata_with_loose` (line 3042). Preserving `read_loose_id` on `_review_attestation_refusal` and `_deferred_ids_refusal` preserves both transition attestation gates. No security finding.

### Step R4

- Checked: boundary semantics and anti-regression tests for `specs.validate_spec`, `backlog.validate_item`, `specs.run_migrate`, `specs._review_attestation_refusal`, `specs._deferred_ids_refusal`, and `spec_citations.stale_spec_anchors`.
- Found: `specs.validate_spec` scans all lines before `## `, whereas `backlog.validate_item` stops at the first non-blank non-`- ` line (pinned by `tests/test_backlog_metadata_duplicate_and_gate_summary.py::test_sub_bullet_boundary_deliberate_non_finding`), requiring a `leading_block_only` parameter on `list_metadata_bullets` (`PR-002`); and `E-02` did not map the six individual call sites onto strict `read_text(...).id6` vs. `read_loose_id` vs. `list_metadata_bullets` (`PR-004`). All fixed in place.

### Step R5

- Checked: evaluated through all eight personas (QA/QC, Testing and regression, UI/UX, Architect, Software engineer, Power user, Novice, Stakeholder) by reference to `.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas`.
- Key persona catches already mapped to findings: QA/QC caught the `backlog` indented sub-bullet boundary trap (`PR-002`) and `specs.run_migrate` trailing-prose `- Status:` capture (`PR-004`); Testing/regression caught nonexistent `tests/test_specs.py` (`PR-001`) and missing `@pytest.mark.core` / bare pytest (`PR-006`); Architect caught over-scoped `migrations/chain.py` (`PR-003`) and `vl7ybn` partial-coverage honesty (`PR-005`).

### Step R6

- Checked: evaluated whether `fkvrc7` should be split.
- Conclusion: no split needed. `fkvrc7` is a focused Order 303 child plan (4 production files, 2 test files, 4 E-items, `Size assessment: standard`) split from `rgva3w` per maintainer decision 2026-11-25 for one single concern (`ebbfmn` + the `vl7ybn` helper).

### Step R7

- Checked: alignment with `Set: metastore` orchestrator `63ib9r` (`E-215`, row 303), downstream `9o83cr` (`- Item-Dependencies: ... executed:fkvrc7`, `E-14`/`V-14` `^-` regex audit), downstream `cxxmyv`, and parallel siblings `wgn3bl`, `t3t7za`, `75jciz`.
- Found: `migrations/chain.py` had zero `^-` regexes and its only metadata regex (`_WORKFLOW_HISTORY_RE`) is owned by `wgn3bl` (`PR-003`); removing it from `fkvrc7` eliminates an unnecessary file overlap.

### Step S5

- Checked: `## Open questions` (`None`). Every finding (`PR-001..PR-007`) has `Overall:Low` remediation risk and is resolved from repository evidence. Three reversible review decisions are recorded in `### Decisions` (`D-1..D-3`). No blocking or human-owned question remains; outcome JSON records `{"questions": []}`.

### Pass 2

- Re-checked the complete revised plan after `- Scope-Paths:` edits (removed `migrations/chain.py`, replaced `tests/test_specs.py` with `tests/test_specs_metadata_duplicate_bullet.py`): front matter, `## Workflow history`, `## Goal`, `E-01..E-04`, `## Project conventions discovered (Step 0)`, `## Findings`, `## Proposed changes` with Mermaid `flowchart LR`, `## Deferred / out of scope`, `## Scope check`, `## Required tests / validation`, `## Spec / documentation sync`, `## Open questions`, `V-01..V-04`, and `## Approval and execution gate`.
- Swept for superseded tokens (zero remaining references to nonexistent `tests/test_specs.py`; `migrations/chain.py` removed from `- Scope-Paths:`, `E-02`, `mypy`, and `V-04`, mentioned only as deferred to `wgn3bl`; bare `aw sanitize` updated to `aw sanitize --agent`).
- Verified `4/4` E/V bijection and clean `aw ipd lint --phase review-finalize --agent`.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R1 / R2 / Nonexistent test file | `ls tests/test_specs.py` (no such file); tests/test_specs_metadata_duplicate_bullet.py:1-142; plan `- Scope-Paths:`, `E-03`, `## Required tests / validation`, `V-03` | Plan named `tests/test_specs.py` in `- Scope-Paths:`, `E-03`, `## Required tests / validation`, and `V-03`, but `tests/test_specs.py` does not exist; the actual duplicate-bullet test module is `tests/test_specs_metadata_duplicate_bullet.py`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced `tests/test_specs.py` with `tests/test_specs_metadata_duplicate_bullet.py` in `- Scope-Paths:`, `E-03`, and `V-03`, and listed all 13 real spec, backlog, citation, and `artifact_meta` test modules in `## Required tests / validation` and `V-02`. Recommendation strength: very strong. |
| PR-002 | HIGH | UNDER-SCOPE | R4 / Divergent block-boundary rule | agent_workflows/specs.py:68-71,291-303 (`_metadata_end`, `validate_spec`); agent_workflows/backlog.py:413-422 (`validate_item`); tests/test_backlog_metadata_duplicate_and_gate_summary.py:194-205 (`test_sub_bullet_boundary_deliberate_non_finding`) | `E-01` specified one generic bullet-listing helper without distinguishing `specs` (scans every line before `## `) from `backlog` (stops at the first non-blank non-`- ` line, including indented sub-bullets, explicitly pinned by `test_sub_bullet_boundary_deliberate_non_finding`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified `artifact_meta.list_metadata_bullets(text, *, leading_block_only=False)` in `E-01` with `\n`-only splitting and both boundary modes, using `leading_block_only=True` in `backlog.validate_item` and `False` in `specs.validate_spec` / `run_migrate` (`D-1`). Recommendation strength: very strong. |
| PR-003 | HIGH | OVER-SCOPE | R1 / R7 / Unneeded `migrations/chain.py` in scope | agent_workflows/migrations/chain.py:1-387 (zero `^-` regexes; only `_WORKFLOW_HISTORY_RE` at lines 73, 301); plan `- Scope-Paths:`, `E-02`, `mypy`, `V-04` | Plan included `agent_workflows/migrations/chain.py` in `- Scope-Paths:`, `E-02`, `mypy`, and `V-04`, but `migrations/chain.py` has zero `^-` metadata regexes and its `_WORKFLOW_HISTORY_RE` is owned by sibling `wgn3bl`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed `agent_workflows/migrations/chain.py` from `- Scope-Paths:`, `E-02`, `mypy`, and `V-04`, and noted in `## Deferred / out of scope` that `wgn3bl` owns `migrations/chain.py::_WORKFLOW_HISTORY_RE` (`D-2`). Recommendation strength: very strong. |
| PR-004 | MEDIUM | IN-SCOPE | R4 / Per-site caller mapping | agent_workflows/specs.py:856,904,966,994,1311,1365; agent_workflows/spec_citations.py:214; agent_workflows/artifact_meta.py:5273 (`read_loose_id`) | `E-02` grouped five regexes without mapping all six call sites or distinguishing strict `_SPEC_ID_RE` (`read_text(...).id6`), loose `_SPEC_ID_BULLET_RE` (`read_loose_id`), and `specs.run_migrate`'s raw trailing-prose `- Status:` capture (`list_metadata_bullets`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added an explicit per-site mapping in `E-02` and a 6-row `## Findings` table covering every regex and call site. Recommendation strength: very strong. |
| PR-005 | MEDIUM | IN-SCOPE | R7 / Scope honesty for `vl7ybn` | .aw/records/backlog/open/20261124-vl7ybn-01-vl7ybn-artifact-meta-has-no-public-reader-that-lists-ever.backlog.md:6; agent_workflows/runner_shared.py:5755; agent_workflows/plans_refs.py:96; plan `## Scope check` | Plan claimed to cover every `vl7ybn` item, but `vl7ybn` also names two non-regex callers (`runner_shared._region_bullet_keys`, `plans_refs._check_order_lines`) outside this plan's scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Clarified in `Scope`, `## Scope check`, and `## Deferred / out of scope` (carrier `vl7ybn`) that `fkvrc7` delivers the `artifact_meta` helper while optional refactoring of those two non-regex callers stays carried by `vl7ybn` (`D-3`). Recommendation strength: strong. |
| PR-006 | MEDIUM | IN-SCOPE | R2 / R4 / Core tier, bare pytest, and sanitizer form | plan `E-03`, `E-04`, `V-03`, `V-04`; tests/test_backlog_metadata_duplicate_and_gate_summary.py; tests/test_specs_metadata_duplicate_bullet.py; spec `4sd62s` C10a / AC-1b; AGENTS.md ("Leak-sanitizer awareness") | Neither test module carries `pytestmark = pytest.mark.core`, and `E-04`/`V-04` used bare `aw sanitize` and omitted the bare core `python3 -m pytest` gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required `@pytest.mark.core` on the new behavioral tests in `E-03` and required bare `python3 -m pytest` and `aw sanitize --agent` in `E-04`/`V-04`. Recommendation strength: strong. |
| PR-007 | MEDIUM | IN-SCOPE | R2 / S7 / Gate contract and technical writing req. 12 | plan `## Approval and execution gate`, `## Proposed changes`; .aw/system/workflows/plan-review/steps/s7-finalize.md; .aw/system/workflows/technical-writing/technical-writing.md (requirement 12(a)) | `## Approval and execution gate` omitted prerequisites, open-questions status, scope-fence declaration (`--scope-reason`/`--scope-ack`), safety stop conditions, hard honesty rule, and conditional finalize ownership; and `## Proposed changes` lacked a Mermaid diagram across the 4 modified production modules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the full execution-gate contract, a Mermaid `flowchart LR` matching all migrated callers and `artifact_meta` readers, and qualified `4sd62s` citations. Recommendation strength: very strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter (`Concern`, `Scope`, `Scope-Paths`) | Included `migrations/chain.py` and nonexistent `tests/test_specs.py`; claimed full `vl7ybn` closure | Removed `migrations/chain.py`, replaced `tests/test_specs.py` with `tests/test_specs_metadata_duplicate_bullet.py`, clarified `vl7ybn` boundary | PR-001, PR-003, PR-005 |
| `E-01`, `E-02` | Generic one-liners without boundary rule or per-site mapping | Specified `list_metadata_bullets(text, *, leading_block_only=False)` with `\n`-only splitting and mapped every one of the 6 call sites to `list_metadata_bullets`, `read_text(...).id6`, or `read_loose_id` | PR-002, PR-004 |
| `E-03`, `E-04`, `V-01..V-04`, `## Required tests / validation` | Cited nonexistent `tests/test_specs.py`, `migrations/chain.py`, bare `aw sanitize`, no core marker or bare pytest | Named all 13 existing test modules, added `@pytest.mark.core`, bare `python3 -m pytest`, and `aw sanitize --agent`, and removed `migrations/chain.py` | PR-001, PR-003, PR-006 |
| `## Findings`, `## Proposed changes`, `## Deferred / out of scope` | Two bullets and 3-line list without diagram | Structured 6-row table, Mermaid `flowchart LR`, and `vl7ybn` deferral for non-regex callers | PR-004, PR-005, PR-007 |
| `## Approval and execution gate` | One sentence | Full execution contract (prerequisites, scope fence with `--scope-reason`/`--scope-ack`, safety, honesty, path-scoped commit/never-push, conditional finalize ownership) | PR-007 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `artifact_meta.list_metadata_bullets` handle the boundary difference between `specs` and `backlog`? | Expose `leading_block_only: bool = False`: `False` scans all lines before `## ` (for specs); `True` stops at `## ` or the first non-blank non-`- ` line (for backlog). | Use one single boundary for both (rejected: scanning past non-`- ` breaks `tests/test_backlog_metadata_duplicate_and_gate_summary.py::test_sub_bullet_boundary_deliberate_non_finding`, while stopping at `# Title` breaks specs). | `agent_workflows/specs.py:68-71,291-303`, `agent_workflows/backlog.py:413-422`, `tests/test_backlog_metadata_duplicate_and_gate_summary.py:194-205`. | yes |
| D-2 | Should `fkvrc7` keep `agent_workflows/migrations/chain.py` in scope? | No; remove it from `fkvrc7` because it has zero `^-` regexes and its `_WORKFLOW_HISTORY_RE` is migrated by `wgn3bl`. | Keep it in `fkvrc7` (rejected: creates an unused `- Scope-Paths:` entry and overlaps `wgn3bl`). | `agent_workflows/migrations/chain.py:1-387`, plan `wgn3bl` `E-03`. | yes |
| D-3 | Should `fkvrc7` refactor `runner_shared._region_bullet_keys` and `plans_refs._check_order_lines`? | No; deliver `artifact_meta.list_metadata_bullets` and migrate `specs.py`/`backlog.py` here, keeping optional simplification of those two non-regex helpers carried by `vl7ybn`. | Widen `fkvrc7` into `runner_shared.py` and `plans_refs.py` (rejected: neither has a `^-` regex blocking `9o83cr` `E-14`, and `runner_shared.py` is already modified by `75jciz`). | Backlog `vl7ybn`, `agent_workflows/runner_shared.py:5755`, `agent_workflows/plans_refs.py:96`. | yes |
