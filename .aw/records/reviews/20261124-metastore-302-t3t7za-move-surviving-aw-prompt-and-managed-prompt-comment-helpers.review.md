# Review findings: ipd t3t7za

- Subject-Id: t3t7za
- Subject-Type: ipd
- Reviewed-At: 2026-11-25
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261125T044745Z-2905371`). The target plan `.aw/records/plans/pending/20261124-metastore-302-t3t7za-move-surviving-aw-prompt-and-managed-prompt-comment-helpers.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` findings). The review read spec `4sd62s` (C5, C10a, AC-1), backlog item `iedbnn`, `Set: metastore` orchestrator `63ib9r` and sibling plans `9o83cr`, `wgn3bl`, `fkvrc7`, `75jciz`, and superseded `rgva3w`, plus all six target production modules (`artifact_meta.py`, `prompts.py`, `check_engine.py`, `artifact_rename.py`, `cli.py`, `status_set.py`) and affected tests (`tests/test_prompts_set_surface.py`, `tests/test_readers_check_engine.py`, `tests/test_log_rename_events.py`, `tests/test_writers_create_summary.py`). It found four `HIGH`, three `MEDIUM`, and one `LOW` finding (`PR-001..PR-008`), all `Overall:Low` remediation risk and all fixed in place. No production code or test code was modified.

### Step T

1. Yes; the plan moves public prompt metadata comment helpers and mirror-id reading into `agent_workflows/artifact_meta.py`, deletes the legacy helper functions from `agent_workflows/prompts.py`, and satisfies the `executed:t3t7za` prerequisite of `9o83cr` `E-14` in `Set: metastore`.
2. No; it touches no private-data, commit-lock, worktree-isolation, merge, or sandbox guard modules.
3. Moderate; 4 E-items in 3 task groups across 6 production modules and 1 test module, coordinated inside `Set: metastore`.
4. Yes; `- Scope-Paths:` lists every touched production file and `tests/test_prompts_set_surface.py` (no additional files required because `_METADATA_TRAILER` stays re-exported in `prompts.py`).
5. Yes; mistakes in prompt comment detection, commentless-prompt purity (refusal to mint a comment on commentless prompts), `validate_prompt_content`, or `log_format_id6` mirror id extraction would corrupt prompt files or break `aw check prompts` / `aw rename prompts` / `aw set`.

AW-TIER: complex

### Step R1

- Checked: every cited module and symbol against the repository: `agent_workflows/prompts.py` (`_METADATA_TRAILER` line 70, `_METADATA_ID_RE` line 87, `_existing_id6s` lines 155-183, `has_metadata_comment` line 264, `inject_metadata_id6` line 276, `update_metadata_status` line 323, `inject_metadata_status` line 389), `agent_workflows/artifact_meta.py` (lines 1950-1968, 2154-2162, 2740-2776, 7253-7256, 7448-7582, 7795-7797, 7903-7909), `agent_workflows/check_engine.py::validate_prompt_content` (lines 1927-1990), `agent_workflows/artifact_rename.py` (`_build_rename_events` lines 332-362, `_id6_write_message` lines 386-407, `_read_existing_id6` lines 440-448, `_MIRROR_ID_RE`/`_MANAGED_PROMPT_ID_RE`/`log_format_id6` lines 451-489), `agent_workflows/cli.py` (line 14687; help strings lines 756, 8108, 8122), `agent_workflows/status_set.py` (line 1607), `tests/test_prompts_set_surface.py` (line 247), and `tests/test_writers_create_summary.py` (lines 1503, 1527).
- Found: unmentioned surviving regexes `prompts._METADATA_ID_RE` and two inline `Set:` regexes in `artifact_rename._build_rename_events` plus three `_prompts.has_metadata_comment` callers in `artifact_rename.py` (`PR-001`); six reverse-delegation sites in `artifact_meta.py` importing `prompts` plus `tests/test_prompts_set_surface.py:247` (`PR-004`); and non-parser docstring/Drift/CLI strings matching bare `rg "aw-prompt"` (`PR-005`). All fixed in place.

### Step R2

- Checked: E/V bijection (`4/4`: `E-01..E-04` to `V-01..V-04`, `- Highest E allocated: 4`), dependency chain (`E-01 -> E-02 -> E-03 -> E-04`), `- Item-Dependencies:` (all 5 split parts `0xsx2n`, `e8420v`, `k6jd6l`, `q6epwc`, `snin8q` are `executed`), concrete `V-*` evidence demands, runtime-demonstration reachability (all `V-*` demand `rg`, `pytest`, `mypy`, or `aw sanitize --agent` output, reachable by construction), and `## Approval and execution gate`.
- Found: unsatisfiable zero-hit `rg` demands in `V-01`/`V-02` against non-parser docstrings and user-facing Drift/CLI messages (`PR-005`); vague test list, missing `@pytest.mark.core` marker, missing bare core `python3 -m pytest`, and bare `aw sanitize` (`PR-006`); and incomplete `## Approval and execution gate` (`PR-007`). All fixed in place.

### Step R3

- Checked: moving prompt comment helpers into `artifact_meta.py` adds no external I/O, shell calls, network calls, or privilege bypasses. `prompts.run_new` (line 479) and `cli.py` (line 14674) keep their existing `'-->'` and `'|'` breakout guards on `--summary`, and `has_prompt_metadata_comment` inspects line 1 only so body prose cannot spoof prompt metadata. `read_mirror_id6` reads the leading mirror header only and enforces valid 6-char id6 syntax. No security finding.

### Step R4

- Checked: behavioral contracts and anti-regression invariants for `validate_prompt_content`, `log_format_id6`, `inject_metadata_id6`, `update_metadata_status`, and `_METADATA_TRAILER`.
- Found: `E-02`'s proposed replacement of `validate_prompt_content`'s comment check with `artifact_meta.read_text(..., record_type="prompt")` would misclassify minimal/empty comments lacking `id`/`status` or files with body bullets (`PR-002`); `E-02` did not specify `log_format_id6`'s BOM-tolerant mirror-id contract (`PR-003`); and `E-01` omitted `artifact_meta.py`'s six reverse imports of `prompts` and `prompts.py` deletion vs. alias contract (`PR-004`). All fixed in place.

### Step R5

- Checked: evaluated through all eight personas (QA/QC, Testing and regression, UI/UX, Architect, Software engineer, Power user, Novice, Stakeholder) by reference to `.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas`.
- Key persona catches already mapped to findings: QA/QC caught the `validate_prompt_content` minimal-comment / body-bullet semantic trap (`PR-002`) and BOM handling in `log_format_id6` (`PR-003`); Architect caught the 6 circular `artifact_meta -> prompts` reverse imports (`PR-004`) and the missed `prompts._METADATA_ID_RE` / `artifact_rename` inline `Set:` regexes (`PR-001`); Testing/regression caught `tests/test_prompts_set_surface.py:247`, `tests/test_writers_create_summary.py`, vague test commands, and missing `@pytest.mark.core` (`PR-004`, `PR-006`).

### Step R6

- Checked: evaluated whether `t3t7za` should be split.
- Conclusion: no split needed. `t3t7za` is already a focused Order 302 child plan split from `rgva3w` per maintainer decision 2026-11-25, covering 6 files and 4 well-scoped E-items (`Size assessment: standard`) for one single concern (prompt metadata comment ownership).

### Step R7

- Checked: alignment with `Set: metastore` orchestrator `63ib9r` (`E-214`, row 302), downstream `9o83cr` (`- Item-Dependencies: ... executed:t3t7za`, `E-14`/`V-14` `rg -n "aw-prompt|aw-managed-prompt"` audit), downstream `cxxmyv`, `90iqr1` (user-facing `cli.py` help text), and parallel siblings `wgn3bl`, `fkvrc7`, `75jciz`.
- Confirmed zero overlapping parser ownership across Orders 301-304; recorded `cli.py` help strings in `## Deferred / out of scope` with carrier `90iqr1`.

### Step S5

- Checked: `## Open questions` (`None`). Every finding (`PR-001..PR-008`) has `Overall:Low` remediation risk and is resolved from repository evidence. Three reversible review decisions are recorded in `### Decisions` (`D-1..D-3`). No blocking or human-owned question remains; outcome JSON records `{"questions": []}`.

### Pass 2

- Re-checked the complete revised plan: front matter, `## Workflow history`, `## Goal`, `E-01..E-04`, `## Project conventions discovered (Step 0)`, `## Findings`, `## Proposed changes` with Mermaid `flowchart LR`, `## Deferred / out of scope`, `## Scope check`, `## Required tests / validation`, `## Spec / documentation sync`, `## Open questions`, `V-01..V-04`, and `## Approval and execution gate`.
- Swept for superseded wording (replaced `read_text` comment-detection claim in `E-02` with `has_prompt_metadata_comment`; replaced bare zero-hit `rg` demands in `V-01`/`V-02` with zero parser/writer/regex hit checks; replaced bare `aw sanitize` with `aw sanitize --agent`).
- Verified `4/4` E/V bijection, unchanged `- Scope-Paths:` and E/V ids, and clean `aw ipd lint --phase review-finalize --agent`.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | UNDER-SCOPE | R1 / R4 / Missed surviving prompt regexes | agent_workflows/prompts.py:87,177-182,389 (`_METADATA_ID_RE`, `_existing_id6s`, `inject_metadata_status`); agent_workflows/artifact_rename.py:335-340,358-360,392,443 (`_build_rename_events`, `_id6_write_message`, `_read_existing_id6`) | Plan missed `prompts._METADATA_ID_RE` (used in `_existing_id6s`), `prompts.inject_metadata_status`, two inline `Set:` prompt-comment regexes in `artifact_rename._build_rename_events`, and three `_prompts.has_metadata_comment` callers in `artifact_rename.py`. Leaving them leaves prompt metadata parsers outside `artifact_meta.py`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added deleting `_METADATA_ID_RE` / `inject_metadata_status` and retargeting `prompts._existing_id6s` in `E-01`, and retargeting all three `has_metadata_comment` calls plus both inline `Set:` regexes in `artifact_rename.py` in `E-02` (`D-3`). Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R4 / `validate_prompt_content` behavioral defect | agent_workflows/check_engine.py:1945-1960 (`validate_prompt_content`); agent_workflows/artifact_meta.py:2740-2776; tests/test_readers_check_engine.py:1613-1660 | `E-02` proposed replacing `validate_prompt_content`'s comment-presence check with `artifact_meta.read_text(..., record_type="prompt")`, which can false-negative on a minimal comment lacking `id`/`status` or false-positive on body bullets. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Changed `E-02` to call `artifact_meta.has_prompt_metadata_comment(text)` directly, preserving exact comment-presence semantics (`D-1`). Recommendation strength: very strong. |
| PR-003 | HIGH | IN-SCOPE | R4 / `log_format_id6` mirror-id contract | agent_workflows/artifact_rename.py:451-489 (`_MIRROR_ID_RE`, `_MANAGED_PROMPT_ID_RE`, `log_format_id6`); tests/test_log_rename_events.py:1-120 | `E-02` did not specify how `artifact_rename.log_format_id6` replaces `_MIRROR_ID_RE` and `_MANAGED_PROMPT_ID_RE` while preserving leading UTF-8 BOM `\ufeff` handling for both `---\nid:` and `<!-- aw-managed-prompt: id: ... -->` mirrors. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `artifact_meta.read_mirror_id6(text)` to `E-01` (with BOM support for both mirror forms), wired `log_format_id6` to it in `E-02`, and added behavioral tests in `E-03`. Recommendation strength: very strong. |
| PR-004 | HIGH | UNDER-SCOPE | R1 / R4 / Reverse imports in `artifact_meta.py` and test callers | agent_workflows/artifact_meta.py:2762-2767,7253-7256,7455,7582,7795-7797,7903-7909; tests/test_prompts_set_surface.py:247; tests/test_writers_create_summary.py:1503,1527 | `artifact_meta.py` itself imports `prompts.has_metadata_comment`, `update_metadata_status`, `inject_metadata_id6`, and `_METADATA_TRAILER` at six sites; `tests/test_prompts_set_surface.py:247` calls `prompts.has_metadata_comment`; and `tests/test_writers_create_summary.py` reads `prompts._METADATA_TRAILER`. None were specified in `E-01`/`E-03`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-01` to rewire all six `artifact_meta.py` sites, move `PROMPT_METADATA_TRAILER` into `artifact_meta.py` while keeping `_METADATA_TRAILER` alias in `prompts.py`, and updated `E-03` to retarget `tests/test_prompts_set_surface.py:247` (`D-2`). Recommendation strength: very strong. |
| PR-005 | MEDIUM | IN-SCOPE | R1 / R2 / Unsatisfiable zero-hit `rg` demands | agent_workflows/prompts.py:27,82,467; agent_workflows/check_engine.py:1955; agent_workflows/artifact_rename.py:327,376,382,401,406,433,991; agent_workflows/cli.py:756,8108,8122; plan `V-01`, `V-02` | `V-01` and `V-02` demanded zero total `rg` hits for `aw-prompt` / `aw-managed-prompt`, which is unsatisfiable without breaking user-facing Drift (`check_engine.py:1955`) and rename messages (`artifact_rename.py:401,406,991`) or deleting docstrings. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Refined `V-01`, `V-02`, and `V-04` to require zero parser/writer/regex hits (every remaining hit verified as docstring, comment, or user-facing message) and zero hits for the deleted symbols; deferred `cli.py` help text to `90iqr1`. Recommendation strength: very strong. |
| PR-006 | MEDIUM | IN-SCOPE | R2 / R4 / Test commands, core tier, and sanitizer form | plan `E-03`, `E-04`, `## Required tests / validation`, `V-03`, `V-04`; tests/test_prompts_set_surface.py (no `pytestmark = pytest.mark.core`); spec `4sd62s` C10a / AC-1b; AGENTS.md ("Leak-sanitizer awareness") | `## Required tests / validation` left test files vague ("plus rename and check_engine prompt tests"), `E-03` lacked `@pytest.mark.core`, and `E-04`/`V-04` used bare `aw sanitize` and omitted the bare core `python3 -m pytest` gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named all 12 concrete existing test modules, added `@pytest.mark.core` to the new test class in `E-03`, and added bare `python3 -m pytest` and `aw sanitize --agent` to `E-04`/`V-04`. Recommendation strength: strong. |
| PR-007 | MEDIUM | IN-SCOPE | R2 / S7 / Approval and execution gate contract | plan `## Approval and execution gate` (original lines 134-139); .aw/system/workflows/plan-review/steps/s7-finalize.md | The execution gate had a single sentence and omitted prerequisite dependencies, open-questions status, scope-fence declaration (`--scope-reason`/`--scope-ack`), safety stop conditions, hard honesty rule, and conditional runner vs. hand-executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all required execution-contract clauses to `## Approval and execution gate`. Recommendation strength: very strong. |
| PR-008 | LOW | IN-SCOPE | Proofreading / Technical writing standard req. 12 | .aw/system/workflows/technical-writing/technical-writing.md (requirement 12(a)); plan `## Proposed changes`, `E-01..E-04` | The plan modifies 6 related production components routing onto `artifact_meta.py` without a Mermaid component diagram and omitted qualified `4sd62s` criteria references in task-group headings. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a Mermaid `flowchart LR` in `## Proposed changes` matching all 5 migrated caller modules and `artifact_meta` helpers, qualified `4sd62s` references, and tightened prose. Recommendation strength: strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter (`Concern`, `Scope`) | Named only 3 `prompts.py` helpers, `validate_prompt_content`, and 2 `artifact_rename.py` regexes | Added `prompts._METADATA_ID_RE`, `inject_metadata_status`, `artifact_rename._build_rename_events` `Set:` regexes, `artifact_meta.py` reverse-import cleanup, `read_mirror_id6`, and `cli.py` help-text deferral (`90iqr1`) | PR-001, PR-003, PR-004, PR-005 |
| `E-01`, `E-02` | High-level one-liners; `E-02` pointed `validate_prompt_content` at `read_text` | Numbered per-module instructions naming exact helpers (`has_prompt_metadata_comment`, `inject_prompt_metadata_id6`, `update_prompt_metadata_status`, `read_mirror_id6`), 6 `artifact_meta` reverse-delegation cleanups, BOM support, and `prompts._existing_id6s` / `artifact_rename` `Set:` migrations | PR-001..PR-004 |
| `E-03`, `E-04`, `V-01..V-04`, `## Required tests / validation` | Vague test list, unsatisfiable zero-hit `rg`, bare `aw sanitize`, no core marker or bare pytest | Named 12 concrete test modules, `@pytest.mark.core` test class, `tests/test_prompts_set_surface.py:247` update, parser/writer/regex `rg` check, bare `python3 -m pytest`, and `aw sanitize --agent` | PR-004, PR-005, PR-006 |
| `## Findings`, `## Proposed changes`, `## Deferred / out of scope` | Two bullets and 3-line list without diagram | 6-row verified table, Mermaid `flowchart LR`, and `90iqr1` deferral for `cli.py` help text | PR-001, PR-005, PR-008 |
| `## Approval and execution gate` | One sentence | Full execution contract (prerequisites, scope fence with `--scope-reason`/`--scope-ack`, safety, honesty, path-scoped commit/never-push, conditional finalize ownership) | PR-007 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `check_engine.validate_prompt_content` detect a leading prompt metadata comment? | Call `artifact_meta.has_prompt_metadata_comment(text)` directly. | Infer comment presence from `artifact_meta.read_text(..., record_type="prompt")` fields (rejected: false-negatives on minimal comments without `id`/`status` and false-positives on body bullets). | `agent_workflows/check_engine.py:1945-1960`, `tests/test_readers_check_engine.py:1613-1660`. | yes |
| D-2 | Should `prompts.py` delete its comment helpers or keep delegating wrappers, and what happens to `_METADATA_TRAILER`? | Delete `_METADATA_ID_RE`, `has_metadata_comment`, `inject_metadata_id6`, `update_metadata_status`, and `inject_metadata_status` from `prompts.py`; move `PROMPT_METADATA_TRAILER` into `artifact_meta.py` and keep plain-text `_METADATA_TRAILER` alias in `prompts.py`. | Keep delegating wrappers in `prompts.py` (rejected: preserves legacy API surface outside `artifact_meta`); remove `_METADATA_TRAILER` alias too (rejected: breaks `tests/test_writers_create_summary.py:1503,1527` needlessly and trailer carries no `aw-prompt` pattern). | `agent_workflows/prompts.py:70-73,87,264-389`, `tests/test_writers_create_summary.py:1503,1527`, `tests/test_prompts_set_surface.py:247`. | yes |
| D-3 | Should `t3t7za` also remove `prompts._METADATA_ID_RE` (`_existing_id6s`) and the two inline `Set:` regexes in `artifact_rename._build_rename_events`? | Yes; migrate all three onto `artifact_meta.read_text(first_line, record_type="prompt")` inside `t3t7za`. | Leave them out of scope (rejected: they are prompt-comment metadata parsers inside `t3t7za`'s owned files and violate `4sd62s` C5). | `agent_workflows/prompts.py:87,180`, `agent_workflows/artifact_rename.py:336-340,358-360`, spec `4sd62s` C5 / AC-1. | yes |
