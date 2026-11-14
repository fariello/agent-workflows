# Review findings: plan py2vu9

- Subject-Id: py2vu9
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `cf53a9466` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-126-py2vu9-add-summary-to-aw-ipd-scaffold-and-aw-prompts-new.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` errors, `0` warnings, `2` `IPD-C802` info advisories on line 106), and all four directly related existing test modules passed (`85 passed`: `26` in `test_ipd_schema`, `31` in `test_ipd_authoring`, `22` in `test_prompts_new`, and `6` in `test_prompts_set_surface`). During revision, `aw ipd sync --apply` allocated `E-04`/`V-04` (`agent_workflows/artifact_meta.py::load_legacy_artifact` trailer stripping on `aw-prompt` comments), advancing `- Highest E allocated:` from `03` to `04`. Pass 2 re-checked `E-01`, `E-04`, `E-02`, `E-03` and `V-01`, `V-04`, `V-02`, `V-03`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern, Scope, Scope-Paths, Goal | Omitted `tests/test_ipd_schema.py` and `agent_workflows/artifact_meta.py` from `- Scope-Paths:` and omitted trailer stripping, delimiter refusal, and pre-mint raw validation | Declares `tests/test_ipd_schema.py` and `agent_workflows/artifact_meta.py` in `- Scope-Paths:`, adds `MetadataVocabularyTests.FIELDS` sync, `prompts._METADATA_TRAILER` stripping in `artifact_meta.load_legacy_artifact`, and pre-strip/pre-mint validation | PR-001, PR-002, PR-003. |
| E-01, V-01 | Edited only `ipd_schema.META_RECOGNIZED` and `tests/test_writers_create_summary.py`, breaking `MetadataVocabularyTests` | Defines `META_SHORT_DESCRIPTION = "Short-Description"`, updates `MetadataVocabularyTests.FIELDS` in `tests/test_ipd_schema.py`, and verifies both `test_ipd_schema.py` and the `test_writers_create_summary.py` schema lint case | PR-001. |
| E-04, V-04 (new via `aw ipd sync`) | Absent; `artifact_meta.load_legacy_artifact` appended `prompts._METADATA_TRAILER` onto the final `aw-prompt` field | Strips `prompts._METADATA_TRAILER` before splitting `aw-prompt` fields on the pipe character and verifies `State.short_description` after cache deletion alongside `test_artifact_meta_legacy_write.py` and `test_artifact_meta_cache.py` | PR-002. |
| E-02, E-03, V-02, V-03 | Unspecified `.strip()`/pre-mint ordering, omitted/blank `--summary` behavior, `command_surface` parity tests, prompt comment breakout/delimiter refusals, and `State.short_description` post-cache-deletion checks | Validates raw `--summary` before `.strip()` and before `mint_id6` (exiting `2`), refuses `"-->"` and pipe delimiters on `aw prompts new`, omits `short_description` when `None` or blank, checks `State.short_description` before and after cache deletion, and runs `test_ipd_authoring.py`, `test_prompts_new.py`, and `test_prompts_set_surface.py` | PR-003, PR-004. |
| Step 0, Findings (F-01..F-04), Behavior decisions (D-1..D-3), Proposed changes | Two brief findings, no `Behavior decisions` section, and no diagram | Documents `cf53a9466` evidence (`F-01..F-04`), explicit `D-1..D-3` decisions, and a 4-step `Proposed changes` list with a Mermaid `flowchart TD` diagram | PR-001..PR-005, Technical Writing Standard Requirement 12. |
| Validation and cross-check (line 106), Approval and execution gate | Two em dashes in preamble (`IPD-C802`), copy-pasted `"Every move is pin-first ... where the Behavior decisions name it"` referencing a missing section, and no unsafe-condition stop sentence | Replaced em dashes with commas, replaced the inapplicable move-only clause with accurate regression-module rules referencing `D-1`, and added the unsafe-condition stop sentence | Proofreading (`IPD-C802`), PR-004, PR-005. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `py2vu9` touches six production modules (`ipd_schema.py`, `artifact_meta.py`, `cli.py`, `command_surface.py`, `ipd_authoring.py`, `prompts.py`) and two test modules (`test_ipd_schema.py`, `test_writers_create_summary.py`), bridging CLI parsing, declared command surfaces, plan schema linting, HTML-comment prompt metadata rendering, and legacy cache-rebuild parsing under `4sd62s` 4.2 and AC-36.
2. Yes. Adding `--summary` to `aw prompts new` writes user-supplied text directly inside the line-1 `<!-- aw-prompt: ... -->` HTML comment, creating HTML-comment breakout (`-->`) and key-injection (pipe delimiter) hazards against `prompt-purity-lint` R1/P4 unless refused prior to `mint_id6`.
3. No, bounded within a multi-plan set (`6e93gt` / `xexn45`), coordinated with `n5sxxk` (`ernmom`) and `fekdwv`.
4. No. All eight work `- Scope-Paths:` entries are explicit file paths, not directory globs.
5. Yes. Updating `ipd_schema.META_RECOGNIZED` without `MetadataVocabularyTests.FIELDS` breaks `python3 -m pytest` immediately, and leaving `prompts._METADATA_TRAILER` unstripped in `artifact_meta.load_legacy_artifact` corrupts `State.short_description` on every cache rebuild.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (`4.1`, `4.2 SHORT DESCRIPTION`, `4.2c`, `4.3`, `AC-36`); parent and sibling plans `6e93gt`, `fekdwv`, `bir7xm`, `n5sxxk`, `ernmom`, `7yr827`, and `xexn45`; production modules `agent_workflows/ipd_schema.py`, `agent_workflows/artifact_meta.py`, `agent_workflows/prompts_index.py`, `agent_workflows/cli.py`, `agent_workflows/command_surface.py`, `agent_workflows/ipd_authoring.py`, `agent_workflows/prompts.py`, `agent_workflows/attention_contract.py`, and `agent_workflows/check_engine.py`; and existing test modules `tests/test_ipd_schema.py`, `tests/test_ipd_authoring.py`, `tests/test_prompts_new.py`, and `tests/test_prompts_set_surface.py` (`85 passed`).
- Found `tests/test_ipd_schema.py` two-sided vocabulary guard failure (`PR-001`): `MetadataVocabularyTests::test_the_table_covers_the_whole_recognized_vocabulary` (`tests/test_ipd_schema.py:494`) asserts `tabulated == set(S.META_RECOGNIZED)`. Adding `Short-Description` to `ipd_schema.META_RECOGNIZED` (`E-01`) without updating `MetadataVocabularyTests.FIELDS` fails the core suite immediately, and `tests/test_ipd_schema.py` was absent from `- Scope-Paths:`. Fixed in `- Scope-Paths:`, `E-01`, `V-01`, and `D-1`.
- Found `artifact_meta.load_legacy_artifact` prompt-comment trailer contamination (`PR-002`): unlike `prompts_index._parse_metadata_comment` (`agent_workflows/prompts_index.py:57`), `artifact_meta.load_legacy_artifact` (`agent_workflows/artifact_meta.py:2256`) splits `m_aw.group(1)` on the pipe delimiter without stripping `prompts._METADATA_TRAILER` (`" . This HTML comment is pipeline metadata only; ..."`). Verified live at `cf53a9466` that when `Short-Description: Adds a widget.` is the final comment key, `artifact_meta.read(id6)` returns `"Adds a widget. . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt."` on cache rebuild, directly breaking `E-03`/`V-03` and `4sd62s` AC-36 case 1. Added `agent_workflows/artifact_meta.py` to `- Scope-Paths:` and allocated `E-04`/`V-04` (`D-2`).
- Found prompt HTML-comment breakout and delimiter injection plus pre-mint validation gaps (`PR-003`): `attention_contract.refuse_unsafe_descriptive` (`agent_workflows/attention_contract.py:752`) permits `"-->"` and pipe characters, which break out of `<!-- aw-prompt: ... -->` (`prompt-purity-lint` R1/P4) or inject arbitrary `Key: value` pairs into the comment. Also tightened both commands to validate `raw_summary` before `.strip()` and before `mint_id6` (exit `2`), omit `short_description` when `None` or blank, and preserve `prompts.render_metadata_comment` backward compatibility (`D-2`, `D-3`).

### Step R2

- Checked: `E-*`/`V-*` bijection (`4/4` after `aw ipd sync --apply` allocated `E-04`/`V-04`), dependency edges (`E-01 -> E-02` and `E-01, E-04 -> E-03`), `- Scope-Paths:` completeness (`8` work paths, matching every file touched by `E-01..E-04`), and runtime reachability of all `V-*` checks.
- Found missing regression pins, `command_surface` parity assertions, post-cache-deletion `State.short_description` checks, and an inapplicable PIN-FIRST move clause in `Approval and execution gate` referencing a nonexistent `Behavior decisions` section (`PR-004`). Fixed across `E-01..E-04`, `V-01..V-04`, `Behavior decisions`, and `Approval and execution gate`.

### Step R3

- Checked: `attention_contract.refuse_unsafe_descriptive` (`MAX_DESCRIPTIVE_LEN` 300, newline/CR before `.strip()`, control characters), prompt comment-close (`"-->"`) and field-delimiter (pipe character) refusals before `mint_id6` with exit code `2` and zero disk writes, dry-run preview non-mutation (`run_scaffold` and `prompts.run_new` without `--apply`), and omitted/whitespace-only `--summary` producing `State.short_description is None` with no empty bullet or comment key.

### Step R4

- Checked: `prompt-purity-lint` R1/P4 single-line comment invariant (`<!-- aw-prompt: ... -->\n` on line 1, zero visible bullets, empty content after line 1 both with and without `--summary`), post-cache-deletion `artifact_meta.read(id6)` round-trip fidelity for both plan bullets and prompt comments (`OQ-02`, `4sd62s` AC-36 case 1), right-sizing (`4` `E-*` items, `8` work Scope-Paths, `<=8` named units per item, `0` `IPD-Z603` advisories), and outcome-based testing (`AGENTS.md` no source-pinning rule).

### Step R5

- Checked: QA/QC (`V-01..V-04` concrete pytest commands, exit-2 refusal assertions with empty `git status --porcelain`, post-cache-deletion `State.short_description` assertions, `command_surface` parity, and `aw check all --agent`), Architect (consistent `short_description` event schema across `fekdwv`, `bir7xm`, and `py2vu9`, and backward-compatible `prompts.render_metadata_comment` adapter for `ernmom` F-03), Software Engineer (trailer stripping aligned with `prompts_index._parse_metadata_comment`, `MetadataVocabularyTests.FIELDS` row parity), Security/Input-Boundary Reviewer (HTML-comment breakout `"-->"` and pipe field-injection refused before `mint_id6`), and Modest Executor (four focused items, clear dependencies).

### Step R6

- Checked: `4` `E-*` items in `1` task group across `8` work `- Scope-Paths:` entries (`- Size assessment: standard`). Within `nj8zdp` right-sizing thresholds (`<=5` E-items, `<=8` work Scope-Paths, `<=8` named units per item, `0` `IPD-Z603` advisories from `aw ipd lint --phase review-finalize --agent --verbose`). No further split is required.

### Step R7

- Checked: `- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:g6tw94, executed:n5sxxk, executed:fekdwv` (`tve77h` and `2xwb9b` verified under `.aw/records/plans/executed/`; `7yr827`, `g6tw94`, `n5sxxk`, and `fekdwv` verified under `.aw/records/plans/pending/`, where `n5sxxk` transitively depends on `ernmom` moving `ipd_authoring.run_scaffold` and `prompts.run_new` onto `artifact_meta.create`, and `fekdwv` creates `tests/test_writers_create_summary.py`), sibling `bir7xm` (Order 125, research and adopt `--summary`), `h06gs7` (`aw describe`), and finishing plan `xexn45` (`E-14` docs/changelog sync).

### Step S5

- Checked: pre-existing `OQ-02` (already `Status: resolved`, `Blocking: no`, carried from `6e93gt`); evaluated three engineering choices surfaced by `PR-001..PR-003`.
- Verified from `4sd62s` 4.2, `prompts_index.py`, `backlog.py`, `ernmom` F-03, and `tests/test_ipd_schema.py` at `cf53a9466`: (1) `Short-Description` is optional (`META_RECOGNIZED` only, `required=False` in `MetadataVocabularyTests.FIELDS`) because `--summary` is optional (`4sd62s` 4.2 line 723); (2) `artifact_meta.load_legacy_artifact` must strip `prompts._METADATA_TRAILER` just like `prompts_index._parse_metadata_comment`, while `prompts.run_new` refuses `"-->"` and pipe characters with usage exit `2`; and (3) raw `--summary` is validated before `.strip()` and before `mint_id6` (matching `backlog.run_new`), omitting `short_description` when `None` or blank.
- Recorded all three self-resolved engineering decisions in `### Decisions` (`D-1..D-3`), all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-01`, `E-04`, `E-02`, `E-03` and `V-01`, `V-04`, `V-02`, `V-03` per `steps/s6-rereview.md` rule 1 after `aw ipd sync --apply` allocated `E-04`/`V-04` and tightened `E-01..E-03` and `V-01..V-03`.
- Verified 4-to-4 `E-*`/`V-*` bijection, `- Highest E allocated: 04`, updated `- Scope-Paths:` (`8` work paths), unchanged `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | R1 / R2 / Scope-Paths, E-01, V-01 | `agent_workflows/ipd_schema.py:365`, `tests/test_ipd_schema.py:253`, `tests/test_ipd_schema.py:494` | `tests/test_ipd_schema.py::MetadataVocabularyTests` asserts exact set equality between `MetadataVocabularyTests.FIELDS` and `ipd_schema.META_RECOGNIZED`; registering `Short-Description` in `E-01` without updating `MetadataVocabularyTests.FIELDS` fails `python3 -m pytest` immediately, and `tests/test_ipd_schema.py` was omitted from `- Scope-Paths:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `tests/test_ipd_schema.py` to `- Scope-Paths:` and updated `E-01`/`V-01` (`D-1`) to define `META_SHORT_DESCRIPTION = "Short-Description"`, add the optional row to `MetadataVocabularyTests.FIELDS`, and run `tests/test_ipd_schema.py`. |
| PR-002 | BLOCKER | IN-SCOPE | R1 / R2 / Scope-Paths, E-04, E-03 | `agent_workflows/artifact_meta.py:2256`, `agent_workflows/prompts.py:70`, `agent_workflows/prompts.py:310`, `agent_workflows/prompts_index.py:57` | `artifact_meta.load_legacy_artifact` splits `aw-prompt` comments on the pipe character without stripping `prompts._METADATA_TRAILER` (`" . This HTML comment is pipeline metadata only; ..."`), so `artifact_meta.read(id6)` returns `Short-Description` contaminated with trailer prose after a cache rebuild, failing `E-03`/`V-03` and `4sd62s` AC-36 case 1. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `agent_workflows/artifact_meta.py` to `- Scope-Paths:` and allocated `E-04`/`V-04` (`D-2`) stripping `prompts._METADATA_TRAILER` before splitting on the pipe character in `artifact_meta.load_legacy_artifact`. |
| PR-003 | HIGH | IN-SCOPE | R1 / R3 / E-02, E-03 | `agent_workflows/attention_contract.py:752`, `agent_workflows/prompts.py:30`, `agent_workflows/backlog.py:1219`, `.aw/records/plans/pending/20261109-metastore-123-ernmom-move-the-plan-scaffold-plan-sync-and-prompt-create-writers-o.ipd.md:70` | `attention_contract.refuse_unsafe_descriptive` allows `"-->"` and pipe characters, letting `aw prompts new --summary` break out of `<!-- aw-prompt: ... -->` (`prompt-purity-lint` R1/P4) or inject synthetic `Key: value` pairs; pre-`.strip()` / pre-`mint_id6` refusal ordering (`exit 2`), omitted/blank `--summary` handling, and `prompts.render_metadata_comment` backward compatibility were also unspecified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified pre-`.strip()`, pre-`mint_id6` validation (exit `2`), `"-->"` and pipe-delimiter refusals in `prompts.run_new`, omission of `short_description` when `None` or blank, and optional `short_description` on `prompts.render_metadata_comment` (`D-2`, `D-3`). |
| PR-004 | MEDIUM | IN-SCOPE | R2 / R7 / V-01..V-03, Gate | `tests/test_prompts_new.py:510`, `agent_workflows/command_surface.py:835`, `agent_workflows/command_surface.py:1768`, `.aw/records/plans/pending/20261109-metastore-126-py2vu9-add-summary-to-aw-ipd-scaffold-and-aw-prompts-new.ipd.md:128` | `V-01..V-03` omitted existing regression suites (`test_ipd_authoring.py`, `test_prompts_new.py`, `test_prompts_set_surface.py`), `command_surface` `legacy_flags` parity assertions, and post-cache-deletion `State.short_description` checks, while `Approval and execution gate` contained a copy-pasted PIN-FIRST move sentence referencing a missing `Behavior decisions` section. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added regression modules, `command_surface` parity checks, and post-cache-deletion `State.short_description` assertions to `V-01..V-04`, added `Behavior decisions` (`D-1..D-3`), and replaced the copy-pasted gate sentence plus added the unsafe-condition stop rule. |
| PR-005 | LOW | IN-SCOPE | Proofreading / R6 | `.aw/records/plans/pending/20261109-metastore-126-py2vu9-add-summary-to-aw-ipd-scaffold-and-aw-prompts-new.ipd.md:70`, `.aw/records/plans/pending/20261109-metastore-126-py2vu9-add-summary-to-aw-ipd-scaffold-and-aw-prompts-new.ipd.md:106` | Line 106 contained two em dashes (`IPD-C802`), `Proposed changes` lacked a Requirement 12 diagram, and `Findings` omitted `cf53a9466` evidence for `MetadataVocabularyTests`, `load_legacy_artifact`, and `command_surface`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced em dashes with commas, added a Mermaid `flowchart TD` diagram in `Proposed changes`, and expanded `Findings` (`F-01..F-04`). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `Short-Description` be registered in `agent_workflows/ipd_schema.py` and `tests/test_ipd_schema.py`? | Define `META_SHORT_DESCRIPTION = "Short-Description"` in `ipd_schema.META_RECOGNIZED` (optional, not `META_REQUIRED`) and add `("Short-Description", "META_SHORT_DESCRIPTION", False, ...)` to `tests/test_ipd_schema.py::MetadataVocabularyTests.FIELDS`. | Make `Short-Description` required (invalid because `--summary` is optional under `4sd62s` 4.2 and existing plans omit it); edit only `ipd_schema.py` (fails `MetadataVocabularyTests::test_the_table_covers_the_whole_recognized_vocabulary`). | `agent_workflows/ipd_schema.py:365`, `tests/test_ipd_schema.py:253`, `tests/test_ipd_schema.py:494`, `4sd62s` 4.2 | yes |
| D-2 | How should `aw prompts new --summary` and `artifact_meta.load_legacy_artifact` preserve `aw-prompt` HTML-comment purity and exact round-trip values? | Strip `prompts._METADATA_TRAILER` before splitting on the pipe character in `artifact_meta.load_legacy_artifact`, refuse `"-->"` and pipe characters in `prompts.run_new` with usage exit `2` before `mint_id6`, and add optional keyword `short_description: Optional[str] = None` to `prompts.render_metadata_comment`. | Allow `"-->"` or pipe characters in prompt summaries (breaks out of the line-1 HTML comment violating `prompt-purity-lint` R1/P4 or injects synthetic comment keys); leave `load_legacy_artifact` unchanged (contaminates `State.short_description` with trailer prose on cache rebuild). | `agent_workflows/artifact_meta.py:2256`, `agent_workflows/prompts.py:30`, `agent_workflows/prompts.py:310`, `agent_workflows/prompts_index.py:57`, `ernmom` F-03 | yes |
| D-3 | In what order should `aw ipd scaffold` and `aw prompts new` validate and normalize `--summary`? | Validate `raw_summary` via `attention_contract.refuse_unsafe_descriptive(..., bound_length=True)` BEFORE `.strip()` and BEFORE `mint_id6` (exiting `2` with no file written), and omit `"short_description"` from `create` `fields` when `--summary` is `None` or whitespace-only after validation (`State.short_description is None`). | Strip before validating (silently accepts trailing `\n`/`\r` instead of refusing, diverging from `backlog.run_new`); emit an empty `- Short-Description:` bullet when omitted or blank (violates `4sd62s` 4.2 optional field semantics). | `agent_workflows/backlog.py:1219`, `agent_workflows/attention_contract.py:752`, `4sd62s` 4.2 and AC-36 case 1 | yes |
