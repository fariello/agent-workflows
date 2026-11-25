# Review findings: ipd 75jciz

- Subject-Id: 75jciz
- Subject-Type: ipd
- Reviewed-At: 2026-11-25
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261125T044745Z-2905371`). The target plan `.aw/records/plans/pending/20261124-metastore-304-75jciz-replace-scope-paths-bullet-writer-and-widened-front-matter-r.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `1` info `IPD-Z603` for the declared size exception). The review read spec `4sd62s` (C5, C10a, AC-1, N3), backlog items `avze51` and `hmtpj2`, `Set: metastore` orchestrator `63ib9r` and sibling plans `9o83cr`, `wgn3bl`, `t3t7za`, `fkvrc7`, and superseded `rgva3w`, plus all eight target production modules (`artifact_meta.py`, `artifact_refs.py`, `partition.py`, `review_basis.py`, `check_engine.py`, `coverage_record.py`, `attention.py`, `runner_shared.py`), ran the widened multiline/flag `rg -U` search over all seven non-`artifact_meta` modules, and checked `tests/test_artifact_refs_rewrite.py`. It found five `HIGH` and two `MEDIUM` findings (`PR-001..PR-007`), all `Overall:Low` remediation risk and all fixed in place. No production code or test code was modified.

### Step T

1. Yes; the plan adds four public helpers to `agent_workflows/artifact_meta.py` (`extract_detail_fields`, `read_multiline_bullets`, `read_review_subject_id`, `neutralize_front_matter_bullets`), rewrites `artifact_refs.apply_scope_path_reference_rewrites` onto `artifact_meta`, removes surviving front-matter regexes across 7 modules, and satisfies the `executed:75jciz` prerequisite of `9o83cr` `E-14` in `Set: metastore`.
2. Yes; it touches `agent_workflows/runner_shared.py::sanitize_front_matter_text` (`_PROPOSAL_BULLET_RE`), which neutralizes untrusted agent-submitted proposal and question text against forging top-level front-matter bullets (`- Status:`, `- Readiness:`, `- Approval:`, `- Id:`).
3. Yes; cross-cutting across 8 production modules and multiple subsystems inside `Set: metastore`.
4. Yes; `- Scope-Paths:` declares all 8 production files, `tests/test_partition.py`, and the plan file itself.
5. Yes; mistakes in `Scope-Paths` rewriting corrupt pending plans or stale begin receipts, mistakes in `sanitize_front_matter_text` allow front-matter injection, mistakes in `attention._extract_detail` strip `--details` summaries on plans and specs, and mistakes in `coverage_record.read` or `_build_review_index` break orchestrator coverage and review-escalation gates.

AW-TIER: complex

### Step R1

- Checked: every cited module, symbol, and regex against the repository: `agent_workflows/artifact_refs.py` (`_SCOPE_PATHS_LINE_RE` line 802, `plan_scope_path_reference_rewrites` lines 933-1007, `apply_scope_path_reference_rewrites` lines 1010-1055), `agent_workflows/partition.py` (`_ORCHESTRATOR_KIND_RE` line 298, `_is_orchestrator_plan` lines 301-312), `agent_workflows/review_basis.py::_is_orchestrator_text` (lines 154-158), `agent_workflows/check_engine.py` (`_REVIEW_SUBJECT_ID_RE` line 9228 / `_build_review_index` line 10773, `_TARGET_BULLET_RE` line 9919 / `parse_cited_spec_ids` lines 9930-9965), `agent_workflows/coverage_record.py` (`_FINGERPRINT_LINE_RE` line 29, `_CHECKED_LINE_RE` line 32, `read` lines 57-108), `agent_workflows/attention.py` (`_FIELD_PATTERNS` lines 413-419, `_extract_detail` lines 440-478), `agent_workflows/runner_shared.py` (`_PROPOSAL_BULLET_RE` line 30263, `sanitize_front_matter_text` lines 30268-30277), `agent_workflows/artifact_meta.py` (lines 3614-3685, 6674-6699, 7373-7385), and the widened `rg -U` output over all 7 non-`artifact_meta` files.
- Found: `check_engine._TARGET_BULLET_RE` has no separate "Scope-Paths branch" (`PR-002`); `attention._FIELD_PATTERNS` covers `scope`, `concern`, and `question` which `artifact_meta.read_text` does not expose (`PR-001`); `runner_shared._PROPOSAL_BULLET_RE` is already clearly a front-matter bullet grammar sanitizer (`PR-005`); and the widened `rg -U` hits also include N3 body-prose / history-record / table-separator regexes that must be explicitly classified (`PR-006`). All fixed in place.

### Step R2

- Checked: E/V bijection (`4/4`: `E-01..E-04` to `V-01..V-04`, `- Highest E allocated: 4`), dependency chain (`E-01 -> E-02 -> E-03 -> E-04`), `- Item-Dependencies:` (all 5 split parts `0xsx2n`, `e8420v`, `k6jd6l`, `q6epwc`, `snin8q` are `executed`), concrete `V-*` evidence demands, runtime-demonstration reachability (all `V-*` demand `pytest`, `mypy`, `rg`, or `aw sanitize --agent` output, reachable by construction), and `## Approval and execution gate`.
- Found: vague test command ("plus citation-rewrite tests"), missing `@pytest.mark.core`, missing bare `python3 -m pytest`, bare `aw sanitize`, unspecified widened `rg -U` command (`PR-006`), and incomplete `## Approval and execution gate` (`PR-007`). All fixed in place.

### Step R3

- Checked (full form, triggered both by `complex` tier and by tier question 2 = Yes):
  - Trust-boundary input neutralization: `runner_shared.sanitize_front_matter_text` (`_PROPOSAL_BULLET_RE`) protects records against untrusted proposal/question payloads injecting top-level front-matter bullets (`- Status:`, `- Readiness:`, `- Approval:`, `- Id:`). Moving the exact regex into `artifact_meta.neutralize_front_matter_bullets(text)` and delegating `sanitize_front_matter_text` to it preserves the two-space indentation defense identically, pinned by `E-03` behavioral tests (`PR-005`).
  - Gate integrity: `check_engine._build_review_index` backs `check.review-finding-unescalated` and `coverage_record.read` backs orchestrator coverage gates; preserving exact `Subject-Id` validation and `"by host-default"` normalization avoids silently disabling either gate (`PR-003`).
  - No new I/O, shell calls, network calls, secrets, or privilege bypasses are introduced.

### Step R4

- Checked: behavioral contracts and anti-regression invariants across all 7 migrated modules against `artifact_meta.py` and existing tests.
- Found: `attention._extract_detail` requires a dedicated `artifact_meta.extract_detail_fields(text)` helper to preserve `Summary -> Scope -> Concern -> Question -> Title` bullet-over-YAML cascade (`PR-001`); `check_engine.parse_cited_spec_ids` requires `artifact_meta.read_multiline_bullets(plan_text, ("Concern", "Scope", "Scope-Paths"))` for multiline continuations (`PR-002`); `coverage_record.read` already holds `state` from `artifact_meta.read_text` and must preserve `" by "` splitting and `"by host-default"` fallback (`PR-003`); `artifact_refs.apply_scope_path_reference_rewrites` must use `artifact_meta.render_legacy_text` with `history=False` and `_core.atomic_write(..., prefix=prefix)` to preserve `grandfathered` skipping, `prefix`, and byte-identical prose/fences (`PR-004`); and `runner_shared._PROPOSAL_BULLET_RE` should be resolved directly into `artifact_meta.neutralize_front_matter_bullets` rather than deferred to an execution-time audit (`PR-005`). All fixed in place.

### Step R5

- Checked: evaluated through all eight personas (QA/QC, Testing and regression, UI/UX, Architect, Software engineer, Power user, Novice, Stakeholder) by reference to `.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas`.
- Key persona catches already mapped to findings: QA/QC caught the `attention._extract_detail` field-loss bug (`PR-001`), `parse_cited_spec_ids` multiline continuation loss (`PR-002`), and `coverage_record.read` `"by host-default"` normalization (`PR-003`); Security / Architect caught the `sanitize_front_matter_text` trust-boundary requirement (`PR-005`) and `artifact_refs` `history=False` / `prefix` contract (`PR-004`); Testing/regression caught the missing concrete test modules, `@pytest.mark.core`, bare `python3 -m pytest`, and exact widened `rg -U` command (`PR-006`).

### Step R6

- Checked: evaluated whether `75jciz` should be split.
- Conclusion: no further split needed. `75jciz` is already a focused Order 304 child plan split from `rgva3w` per maintainer decision 2026-11-25, wired into orchestrator `63ib9r` (`E-216`), `9o83cr`, and `cxxmyv`, with 4 concise E-items covering one cohesive concern (`avze51` + `hmtpj2` front-matter regexes).

### Step R7

- Checked: alignment with `Set: metastore` orchestrator `63ib9r` (`E-216`, row 304), downstream `9o83cr` (`- Item-Dependencies: ... executed:75jciz`, `E-14`/`V-14` AC-1 audit), downstream `cxxmyv`, and parallel siblings `wgn3bl`, `t3t7za`, `fkvrc7`.
- Confirmed zero overlapping parser ownership across Orders 301-304; documented `hmtpj2`'s non-front-matter history/OQ-row grammar items (`ipd_lint._HISTORY_ATTRIB_RE`, `_COVERAGE_HIST_RE`, `plan_readiness._HISTORY_RECORD_PARTS_RE`, `review_findings._OQ_FINDING_REF_RE`) and final widened audit as carried by `9o83cr`.

### Step S5

- Checked: `## Open questions` (`None`). Every finding (`PR-001..PR-007`) has `Overall:Low` remediation risk and is resolved from repository evidence. Three reversible review decisions are recorded in `### Decisions` (`D-1..D-3`). No blocking or human-owned question remains; outcome JSON records `{"questions": []}`.

### Pass 2

- Re-checked the complete revised plan: front matter, `## Workflow history`, `## Goal`, `E-01..E-04`, `## Project conventions discovered (Step 0)`, `## Findings` (8-row table plus classified N3/history/table-separator list), `## Proposed changes` with Mermaid `flowchart LR`, `## Deferred / out of scope`, `## Scope check`, `## Required tests / validation`, `## Spec / documentation sync`, `## Open questions`, `V-01..V-04`, and `## Approval and execution gate`.
- Swept for superseded wording (removed inaccurate "metadata Scope-Paths branch" description of `_TARGET_BULLET_RE`; replaced open "audit" of `_PROPOSAL_BULLET_RE` with concrete delegation to `artifact_meta.neutralize_front_matter_bullets`; replaced bare `aw sanitize` with `aw sanitize --agent`).
- Verified `4/4` E/V bijection, unchanged `- Scope-Paths:` and E/V ids, and clean `aw ipd lint --phase review-finalize --agent`.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R4 / `attention._extract_detail` field loss | agent_workflows/attention.py:413-478 (`_FIELD_PATTERNS`, `_extract_detail`); agent_workflows/artifact_meta.py:3614-3685 | `attention._extract_detail` cascades `Summary -> Scope -> Concern -> Question -> Title` with bullet-over-YAML precedence, but `artifact_meta.read_text` does not register `scope`, `concern`, or `question`. Pointing `_extract_detail` directly at `read_text` would silently drop `--details` summaries on plans and specs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `artifact_meta.extract_detail_fields(text)` in `E-01` preserving exact cascade and bullet-over-YAML precedence, and delegated `attention._extract_detail` to it in `E-02` (`D-1`). Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R1 / R4 / `check_engine._TARGET_BULLET_RE` multiline contract | agent_workflows/check_engine.py:9919-9965 (`_TARGET_BULLET_RE`, `parse_cited_spec_ids`); plan `Scope`, `E-02` | Plan inaccurately described `_TARGET_BULLET_RE` as having a "metadata Scope-Paths branch", when it is one regex matching `Concern`, `Scope`, and `Scope-Paths` plus multiline continuation lines, which `artifact_meta.read_text` does not expose. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `artifact_meta.read_multiline_bullets(text, keys)` in `E-01` and migrated `check_engine.parse_cited_spec_ids` onto it in `E-02`, correcting the description throughout (`D-2`). Recommendation strength: very strong. |
| PR-003 | HIGH | IN-SCOPE | R4 / `coverage_record`, `review_basis`, `partition`, and `check_engine._REVIEW_SUBJECT_ID_RE` contracts | agent_workflows/coverage_record.py:29-80 (`read`); agent_workflows/check_engine.py:9228,10773 (`_REVIEW_SUBJECT_ID_RE`, `_build_review_index`); agent_workflows/partition.py:298-312; agent_workflows/review_basis.py:154-158 | `E-02` did not specify how `coverage_record.read` reuses its existing line-65 `artifact_meta.read_text` state while preserving `" by "` splitting and `"by host-default"` fallback, how `_REVIEW_SUBJECT_ID_RE` is replaced, or case-insensitive `plan_role` matching for `partition` and `review_basis`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified exact per-module replacements in `E-02` (including `artifact_meta.read_review_subject_id(text)` in `E-01`, reusing `state.fields` with `"by host-default"` normalization in `coverage_record.read`, and case-insensitive `plan_role` lookup in `partition` and `review_basis`). Recommendation strength: very strong. |
| PR-004 | HIGH | IN-SCOPE | R4 / `artifact_refs` `Scope-Paths` write contract | agent_workflows/artifact_refs.py:802,933-1055 (`_SCOPE_PATHS_LINE_RE`, `plan_scope_path_reference_rewrites`, `apply_scope_path_reference_rewrites`); agent_workflows/artifact_meta.py:6693,7373-7385; tests/test_artifact_refs_rewrite.py:810-865 | `E-01` did not specify preserving `grandfathered` skipping, forward-declaration skipping, `prefix=prefix`, byte-identical prose/fences, and no workflow-history append (`history=False`) when moving `artifact_refs.py` onto `artifact_meta`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-01` to read via `artifact_meta.read_text` + `ipd_schema.parse_scope_paths` and write via `artifact_meta.render_legacy_text` (`history=False`, reusing `_LEGACY_BULLET_LABEL["scope_paths"]`) + `_core.atomic_write(..., prefix=prefix)`. Recommendation strength: very strong. |
| PR-005 | HIGH | IN-SCOPE | R1 / R3 / R4 / Unresolved execution-time audit on `_PROPOSAL_BULLET_RE` | agent_workflows/runner_shared.py:30263-30277 (`_PROPOSAL_BULLET_RE`, `sanitize_front_matter_text`); plan `Scope`, `E-02` | Plan left `runner_shared._PROPOSAL_BULLET_RE` as an execution-time audit, whereas static reading settles that `sanitize_front_matter_text` encodes the front-matter bullet line grammar to block front-matter injection in untrusted proposals and questions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `artifact_meta.neutralize_front_matter_bullets(text)` in `E-01`, delegated `runner_shared.sanitize_front_matter_text` to it in `E-02`, and added behavioral tests in `E-03` (`D-3`). Recommendation strength: very strong. |
| PR-006 | MEDIUM | IN-SCOPE | R2 / R4 / Concrete test suites, widened `rg -U` command, core tier, and sanitizer form | plan `E-03`, `E-04`, `## Required tests / validation`, `V-02..V-04`; widened `rg -U` output over 7 files; tests/test_partition.py | Validation left citation-rewrite tests vague, omitted `@pytest.mark.core`, omitted bare `python3 -m pytest`, used bare `aw sanitize`, and did not state the exact widened `rg -U` command or classify surviving N3/history/table-separator hits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named all 12 concrete test modules, added `@pytest.mark.core` to `E-03`, added bare `python3 -m pytest` and `aw sanitize --agent` to `E-04`/`V-04`, stated the exact widened `rg -U` command, and listed every classified N3/history/table-separator hit in `## Findings`. Recommendation strength: strong. |
| PR-007 | MEDIUM | IN-SCOPE | R2 / S7 / Gate contract and technical writing req. 12 | plan `## Approval and execution gate`, `## Proposed changes`; .aw/system/workflows/plan-review/steps/s7-finalize.md; .aw/system/workflows/technical-writing/technical-writing.md (requirement 12(a)) | `## Approval and execution gate` omitted prerequisites, open-questions status, scope-fence declaration (`--scope-reason`/`--scope-ack`), safety stop conditions, hard honesty rule, and conditional finalize ownership; `## Proposed changes` lacked a Mermaid diagram across the 8 modified production modules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the full execution-gate contract, a Mermaid `flowchart LR` matching all 7 migrated caller modules and `artifact_meta` helpers, and qualified `4sd62s` citations. Recommendation strength: very strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter (`Concern`, `Scope`) | Inaccurate `_TARGET_BULLET_RE` "Scope-Paths branch" wording; open audit on `_PROPOSAL_BULLET_RE` | Named all 4 new `artifact_meta` helpers, corrected `_TARGET_BULLET_RE` description, resolved `_PROPOSAL_BULLET_RE` to `neutralize_front_matter_bullets`, listed N3/history exclusions | PR-001, PR-002, PR-005, PR-006 |
| `E-01`, `E-02` | High-level one-liners without helper specs or per-module contracts | Specified exact 4 `artifact_meta` helpers, `artifact_refs` `render_legacy_text` (`history=False`) + `prefix` contract, and numbered per-module migrations across all 6 `E-02` modules | PR-001..PR-005 |
| `E-03`, `E-04`, `V-01..V-04`, `## Required tests / validation` | Vague test list, unspecified widened `rg -U`, bare `aw sanitize`, no core marker or bare pytest | Named all 12 concrete test modules, added `@pytest.mark.core`, exact widened `rg -U` command with explicit symbol checks, bare `python3 -m pytest`, and `aw sanitize --agent` | PR-006 |
| `## Findings`, `## Proposed changes`, `## Deferred / out of scope` | Two bullets and 3-line list without diagram | 8-row verified table plus classified N3/history/table-separator list, Mermaid `flowchart LR`, and `9o83cr` deferral for `hmtpj2` non-front-matter audit | PR-001..PR-007 |
| `## Approval and execution gate` | One sentence plus size-exception rationale | Updated cohesion rationale and full execution contract (prerequisites, scope fence with `--scope-reason`/`--scope-ack`, safety, honesty, path-scoped commit/never-push, conditional finalize ownership) | PR-007 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `attention._extract_detail` replace `_FIELD_PATTERNS` without losing `Scope`, `Concern`, or `Question` details? | Add `artifact_meta.extract_detail_fields(text)` implementing the `Summary -> Scope -> Concern -> Question -> Title` bullet-over-YAML cascade, and delegate `attention._extract_detail` to it. | Read from `artifact_meta.read_text(text).fields` directly (rejected: `read_text` does not register `scope`, `concern`, or `question`, which would strip `--details` on plans and specs). | `agent_workflows/attention.py:413-478`, `agent_workflows/artifact_meta.py:3614-3685`. | yes |
| D-2 | How should `check_engine.parse_cited_spec_ids` replace `_TARGET_BULLET_RE` without losing multiline continuation lines? | Add `artifact_meta.read_multiline_bullets(text, keys)` and call it with `("Concern", "Scope", "Scope-Paths")`. | Read scalar fields from `artifact_meta.read_text` (rejected: `read_text` does not return raw `Concern`/`Scope` text or multiline continuations). | `agent_workflows/check_engine.py:9919-9965`. | yes |
| D-3 | Should `runner_shared._PROPOSAL_BULLET_RE` be moved into `artifact_meta.py` or classified as body prose? | Move it into `artifact_meta.neutralize_front_matter_bullets(text)` and delegate `runner_shared.sanitize_front_matter_text` to it. | Leave it in `runner_shared.py` as an exclusion (rejected: its regex explicitly encodes the front-matter `- <Key>:` line grammar, so moving it into `artifact_meta.py` keeps the front-matter grammar single-sourced under `4sd62s` C5). | `agent_workflows/runner_shared.py:30263-30277`, spec `4sd62s` C5. | yes |
