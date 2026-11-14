# Review: bir7xm - Write short_description at creation for research and adopt

- Subject-Id: bir7xm
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

#### Changes
- Replaced the two em dashes (`U+2014`) in the `## Validation and cross-check` reachability sentence with commas (`IPD-C802`).
- Added a Requirement 12(b) `mermaid` `flowchart TD` in `## Proposed changes (ordered, validatable)` showing both commands, the shared refusal check, and the with-key and without-key create paths, plus one sentence explaining why `E-03` runs first.
- Rewrote the one-line `## Proposed changes` entries so each names the module and symbol it changes.
- Split the `## Findings` evidence header so the 2026-11-09 and 2026-11-14 measurements carry their own commit.

#### Issues
- None remaining after revision; checked against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`. Recommendation strength for the remaining prose: strong.

### Step T

1. Yes. The plan adds an on-disk key (`short-description:`) to research YAML front matter, a file format other tools read (`research_contract.parse_frontmatter`, `artifact_meta._parse_yaml_front_matter`); it changes no spec and no CLI option.
2. No. It touches no leak, commit, worktree, merge, or sandbox code; it relies on existing descriptive-value refusals and does not change them.
3. No. 3 single-concern `E-*` items after revision in one task group, across `agent_workflows/artifact_meta.py`, `agent_workflows/research_cmd.py`, and `agent_workflows/artifact_adopt.py`.
4. Yes. 4 work `Scope-Paths` plus the plan file; the review found one missing work unit (the create-time YAML rendering, now `E-03`) inside the declared `agent_workflows/artifact_meta.py`.
5. Low to moderate. A wrong position or an unconditional key changes the bytes of every new research document, but the change is additive and reversible, and no pinned test compares full front matter bytes.

AW-TIER: standard

### Step R1

- Checked: `agent_workflows/research_cmd.py` (`plan_new`, `run_new`, `_refuse_unsafe_descriptive`, `build_frontmatter`, `_emit_new_error`, `plan_new_comparison`, `_compose_comparison_summary`), `agent_workflows/artifact_adopt.py` (`SUPPORTED_TYPES`, `AdoptionPlan`, `plan_adoption`, `_first_heading`, `apply_adoption`, `run_adopt`), `agent_workflows/artifact_meta.py` (`_COMMON_FIELDS`, `REGISTRY["research"]`, `validate_new_events`, `_check_string_safety`, `_parse_yaml_front_matter`, `load_legacy_artifact`), `agent_workflows/research_contract.py` (`FRONTMATTER_FIELDS`, `validate_frontmatter`), `agent_workflows/attention_contract.py` (`refuse_unsafe_descriptive`, `_is_safe_descriptive_bounded`), `agent_workflows/cli.py` (`--summary` on `p_research_new`, `p_research_cmp`, `p_adopt`), and spec `4sd62s` 4.2 SHORT DESCRIPTION and AC-36.
- The original `E-02` said adopt renders a `- Short-Description:` bullet. `artifact_adopt.SUPPORTED_TYPES = ("research",)` and the adopted front matter comes from `research_cmd.plan_new`, so the on-disk form is the YAML key (`PR-001`).
- The original `E-01` named `research_cmd.run_new` as the place the field enters the `create` event, but after `s95hj6` E-01 the front matter is rendered in `plan_new` through `artifact_meta.create(..., dry_run=True)`; `run_new` only parses arguments and calls `plan_new` (`PR-002`).
- `plan_adoption` passes `summary=summary or heading_text or suggestion.slug` to `plan_new`, so wiring `summary` straight into `short_description` would write a derived value, which spec 4.2 forbids ("written only by tools (--summary on the creating command, or a setter)") (`PR-003`).

### Step R2

- Checked: the `E-*`/`V-*` bijection (`E-01..E-03` <-> `V-01..V-03` after `aw ipd sync --apply` assigned `E-03` and advanced the watermark to `03`), `- Scope-Paths:` completeness, the `- Item-Dependencies:` chain, and `aw ipd lint --phase author --agent` (2 `IPD-C802` info before revision) and `--phase review-finalize --agent` (`clean`, 0 findings after).
- `s95hj6` E-03 and `x2dxvf` E-04 render only the spec-5.8 keys plus `priority` on research create, and `s95hj6` D-2 covers only in-place `set`; no plan rendered `short-description` at creation. Added `E-03` in the already declared `agent_workflows/artifact_meta.py` (`PR-004`).
- The gate said "the named existing modules run green" but no module was named. Added a PIN-FIRST rule with the command (the `s95hj6` pattern) and named modules per V-item; the eight research and adopt modules report `140 passed` at `aadf6adf7` (`PR-005`).
- `V-01` and `V-02` did not unlink `.aw/state/index.db` before `read`, so they could pass against a stale cache, and `V-02` demanded an `aw check all` case that `E-02` never asked for. Both now match their E-items (`PR-006`).
- `s95hj6` and `x2dxvf` are not listed directly, but `executed:n5sxxk` depends on both, so the ordering edge holds transitively; no change.

### Step R3

- Checked: the `--summary` refusal path on both commands, including adopt `--allow-leaks`, where `x2dxvf` sets `migration_import=True` and `artifact_meta._check_string_safety` returns early. The `plan_new` pre-mint refusal (`bound_length=True`, 300 characters, newline, control character) still runs on that path, so `E-02` names it as the gate; `E-01` requires the same check on any `short_description` a caller passes that differs from `summary`, so a future caller cannot bypass it (`PR-003`).
- `artifact_meta.validate_new_events` always runs `_check_leak_sanitizer` on string fields, so the new field gets the leak check without plan changes. No secrets, network, or privileged paths are involved.

### Step R4

- Checked: byte stability for documents created without `--summary` (no line, otherwise byte-identical, `E-03`), the key's position relative to the optional `priority:` line (`D-1`, matching `s95hj6` D-2), preview-equals-apply for both commands, read-back after a cache rebuild (F-04), and the required `summary:` key, which stays unchanged.
- Added the omitted-`--summary` case and the derived-heading adopt case so the "only when given" rule is tested, and the inbox-original check so an adopt refusal is shown to lose no data (`PR-007`).
- Added `D-2`: `aw research new-comparison` writes no `short_description`, since spec 4.2 names only `aw research new` and the comparison writes a different composed summary per file (`DEC-002`).

### Step S5

- All eight findings (`PR-001`..`PR-008`) are `IN-SCOPE` or `UNDER-SCOPE` and fixed in place with `Low` remediation risk. Every decision (`DEC-001`..`DEC-003`) is reversible and answered from spec `4sd62s` 4.2 and repository code. No material question requires a human decision (`questions: []`).

### Pass 2

- Re-read `.aw/records/plans/pending/20261109-metastore-125-bir7xm-write-short-description-at-creation-for-research-and-adopt.ipd.md` top to bottom after the revisions and `aw ipd sync --apply`, then filled `V-03`.
- Swept superseded wording: no remaining `- Short-Description:` bullet claim for adopt, no `research_cmd.run_new` claim as the event site, and `## Scope check`, `## Required tests / validation`, and `## Proposed changes` match `E-01` to `E-03` and `D-1` to `D-3`.
- `aw ipd lint --phase review-finalize --agent`: `outcome: clean`, `findings: 0`. Zero em or en dashes, no `TODO` placeholders in E or V items, and `aw sanitize --agent`: `outcome: clean`, `findings: 0`.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | IN-SCOPE | R1 | `agent_workflows/artifact_adopt.py::SUPPORTED_TYPES` (`("research",)`); `agent_workflows/artifact_adopt.py::plan_adoption` (`frontmatter=planned.content` from `research_cmd.plan_new`) | `E-02` said adopt renders a `- Short-Description:` bullet, but adopt only creates research documents with YAML front matter; an executor following it would write a bullet into a YAML-fenced file or invent a second format | Low | FIXED | `E-02` and its expected outcome now render the `short-description:` YAML key through `E-03`; added F-03 |
| PR-002 | HIGH | IN-SCOPE | R1 | `agent_workflows/research_cmd.py::run_new` (calls `plan_new(..., summary=...)`); `s95hj6` E-01 (`plan_new` renders `PlannedFile.content` via `artifact_meta.create(..., dry_run=True)`) | `E-01` named `run_new` as the place the field enters the `create` event; the event is built in `plan_new` | Low | FIXED | `E-01` adds a keyword-only `short_description` parameter to `plan_new`, includes it in the `create` fields, and has `run_new` pass `--summary` |
| PR-003 | HIGH | UNDER-SCOPE | R1 / R3 | `agent_workflows/artifact_adopt.py::plan_adoption` (`summary=summary or heading_text or suggestion.slug`); spec `4sd62s` 4.2 ("written only by tools (--summary on the creating command, or a setter)"); `agent_workflows/artifact_meta.py::_check_string_safety` (returns early when `migration_import`) | Wiring the `summary` argument would store a heading- or slug-derived value as `short_description`, and the plan did not name the refusal gate on the `--allow-leaks` path | Low | FIXED | `E-02` passes only the explicit `--summary` as `short_description` and carries it on `AdoptionPlan`; `D-3` records the rule; `E-01` keeps the `plan_new` pre-mint refusal as the gate for any caller-supplied value |
| PR-004 | HIGH | UNDER-SCOPE | R2 | `s95hj6` E-03 and `x2dxvf` E-04 (create renders spec-5.8 keys plus `priority`); `s95hj6` D-2 (in-place `set` only) | No plan rendered `short-description:` on research creation, so `E-01` and `E-02` had nothing to call | Low | FIXED | Added `E-03`/`V-03` in the declared `agent_workflows/artifact_meta.py`, with the position rule in `D-1`; added F-06 |
| PR-005 | HIGH | IN-SCOPE | R2 | `## Approval and execution gate` ("the named existing modules run green"); no module named anywhere in the plan | Pin-first was required but unexecutable: no command and no module list | Low | FIXED | Added the PIN-FIRST rule with its command and named the modules per V-item (12 modules total); baseline `140 passed` recorded in F-07 |
| PR-006 | MEDIUM | IN-SCOPE | R2 | `V-01`/`V-02` (`artifact_meta.read` with no cache deletion); `V-02` (`aw check all --agent` case absent from `E-02`); `fekdwv` V-01 (unlinks `.aw/state/index.db`) | Read-back could pass from a stale cache, and `V-02` demanded a case its E-item did not request | Low | FIXED | Each V-item unlinks the fixture's `.aw/state/index.db` before `read`, asserts the on-disk line and position, and `E-02` now requests the `aw check all` case |
| PR-007 | MEDIUM | UNDER-SCOPE | R4 | `agent_workflows/cli.py` (`--summary` `default=""` on `p_research_new` and `p_adopt`); `agent_workflows/artifact_adopt.py::_first_heading` | No case proved the field is absent without `--summary`, or that an adopt refusal leaves the inbox original in place | Low | FIXED | Added the omitted-`--summary` case (research), the derived-heading case (adopt), and the inbox-original check on every adopt refusal |
| PR-008 | LOW | IN-SCOPE | Proofreading / R4 | `## Validation and cross-check` (two `U+2014`); OQ-02 `- Owner: none`; `## Approval and execution gate`; `fekdwv` gate | Two `IPD-C802` em dashes, no Requirement 12(b) diagram, no Behavior decisions section, no stop-and-report conditions, and an unowned resolved question | Low | FIXED | Replaced the em dashes, added the `mermaid` flowchart, `## Behavior decisions` (`D-1`..`D-3`), the unsafe-condition stop, and `- Owner: plan author` |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| DEC-001 | Where does the `short-description:` key go in research front matter? | Last line, after `consumed-by:` and the optional `priority:`, before the closing `---` (`D-1`) | Directly after `summary:`; before `priority:` | Matches the `priority` insertion rule of `s95hj6` D-2, so in-place `set` and create agree; `research_contract.validate_frontmatter` ignores key order; no pinned test compares full bytes. Recommendation strength: strong | Yes |
| DEC-002 | Does `aw research new-comparison` write `short_description`? | No (`D-2`) | Write the user `--summary` on every comparison file; write each composed summary | Spec `4sd62s` 4.2 names `aw research new --summary` only; each comparison file gets a different composed summary from `_compose_comparison_summary`. Recommendation strength: moderate | Yes |
| DEC-003 | Does adopt write `short_description` from the summary it derives when `--summary` is omitted? | No; only an explicit non-empty `--summary` (`D-3`) | Write the derived heading or slug | Spec `4sd62s` 4.2: written only by tools from `--summary` or a setter; the migration fills missing values with a model. Recommendation strength: strong | Yes |
