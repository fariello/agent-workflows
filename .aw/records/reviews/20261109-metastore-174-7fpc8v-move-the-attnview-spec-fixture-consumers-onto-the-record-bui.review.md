# Review findings: plan 7fpc8v

- Subject-Id: 7fpc8v
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `7e8f71682` in a non-interactive runner review-sweep lane worktree. The tracked plan was committed and unmodified, so the pre-review snapshot commit was skipped. `aw ipd lint --phase author --agent` returned `clean` (0 findings) before edits, and `aw ipd lint --phase review-finalize --agent` returned `clean` (0 findings) after edits. All four `- Item-Dependencies:` exist (`tve77h` executed; `g5hpbb`, `xexn45`, `j6o96i` pending). `tests/record_builder.py` does not exist yet; `j6o96i` E-01 creates it, and the gate already requires `j6o96i` executed first.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Checklist preamble | Id-carry paragraph naming E-01, E-02, E-10, E-13 as kept ids, none of which is in this plan | States E-22..E-25 come from the `9rgn2w` E-10 split and that E-01/E-13 cited here live in `j6o96i` | PR-004 |
| Checklist preamble (new) | "batch-rule step-2 command" referenced but defined only in `59aiyh` | OUTCOME-LIST COMMAND spelled out with `.aw/state/7fpc8v/<short>-before.txt` / `-after.txt` and the empty-`diff` bar | PR-003 |
| Checklist preamble (new), E-22, E-23, E-24 | "build the nine valid specs with `RecordBuilder.spec(...)` into a temporary directory and iterate" | One NINE-SPEC RECIPE: `text_only=True`, write `<status>.md` into a `tempfile.TemporaryDirectory()`, deferred gate fields, no gate elsewhere, one history record; stop if the builder cannot express it without `raw_fields=` | PR-001, PR-002 |
| E-25, Required tests, all V-items | "batch-rule step-2 command"; "over the five modules" | "OUTCOME-LIST COMMAND"; over each converted module | PR-003 |
| Approval and execution gate | Lifecycle transition without runner/hand-executor ownership | Adds "never a hand `git mv`" and the conditional `aw ipd finalize 7fpc8v` ownership | PR-005 |
| Scope check | "Under-scope: none known." | Notes the recipe now states the validator's gate and history rules | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. Only test modules change; no spec, CLI, output or file-format contract.
2. No. No sanitizer, commit, worktree, merge or sandbox code.
3. No. Four E-items over five test modules in one family.
4. Yes. `- Scope-Paths:` lists the five test modules and the plan.
5. Yes, mildly. A recipe that silently differs from the fixtures could make three regression tests pass vacuously or fail; the outcome-list diff catches a failure but not a vacuous pass, so the recipe must reproduce the validator's rules.

AW-TIER: standard

### Step R1

- Checked: every symbol E-22..E-24 names against HEAD: `tests/test_attention_contract.py::FixtureParseTests.test_valid_specs_have_bare_enum_status_and_map` (globs `FIX / "specs-valid"`), `tests/test_specs_verbs.py::CheckTests.test_valid_specs_pass`, `tests/test_specs_releases_unsafe_field.py` `test_non_regression_valid_specs_fixtures`; `violations/` reads present in all three (V-22..V-24 are satisfiable); `tests/test_attention.py` and `tests/test_attention_stem.py` read no fixture (only prose `attnview` hits), matching F-42.
- Found "batch-rule step-2 command" defined only in `.aw/records/plans/pending/20261102-metastore-10-59aiyh-move-test-data-to-one-shared-record-builder-over-artifact-me.ipd.md` "Batch rule" step 2 (PR-003), and an id-carry paragraph naming ids absent from this plan (PR-004).

### Step R2

- Checked: E/V bijection (4/4), dependency edges (E-25 after E-22..E-24), V-item evidence concreteness, gate execution contract.
- `specs.validate_spec` (`agent_workflows/specs.py::validate_spec`) flags `attention.gate-missing` for a deferred spec without `Gate-Kind`/`Gate-Ref`, `attention.gate-forbidden` for gate fields on any other status, and `attention.history-missing` without a `attention_contract.HISTORY_RECORD_RE` record. The plan's recipe said only "one per status", so a literal executor would fail two of the three tests and, bound by "keep every assertion unchanged", be stuck (PR-001).
- `j6o96i` E-01 PLACEMENT puts a file-form spec under `.aw/records/specs/<status>/` of a repository carrying `.aw/`, which a bare temporary directory is not; "iterate where the test globs" over such a layout is ambiguous. The text form (`text_only=True`, `repo_root=None` allowed) plus writing `<status>.md` keeps the glob and the `f.name` messages identical (PR-002).
- Lifecycle transition lacked runner/hand-executor ownership (PR-005).

### Step R3

- Checked: no production code, no secret or private data, no git operation beyond `aw commit 7fpc8v -- <paths>`; temporary directories are per-test. No security finding.

### Step R4

- Checked: behavior-not-structure rule (tests still call `specs.validate_spec` and `A.class_of` on built files; no source reading); right-sizing (4 E-items, 5 work Scope-Paths, one module per item, within `nj8zdp` guidance); single-recipe definition instead of three diverging copies.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Executability / correctness | `agent_workflows/specs.py::validate_spec` "deferred spec lacks Gate-Kind/Gate-Ref", "gate fields present on a non-deferred spec", "no conformant `## Workflow history` record"; `tests/fixtures/attnview/specs-valid/deferred.md` carries `- Gate-Kind: issue` | The recipe did not state the deferred gate, the no-gate rule for the other eight, or the required history record, so built specs would fail `test_valid_specs_pass` and `test_non_regression_valid_specs_fixtures` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | NINE-SPEC RECIPE rules (a) to (c) with the fixture's gate values; stop if the builder needs `raw_fields=` for valid input. Strength: very strong |
| PR-002 | MEDIUM | IN-SCOPE | Executability | `j6o96i` E-01 PLACEMENT and WRITING rules (file form needs a repository with `.aw/`, places specs in status subdirectories); 7fpc8v E-22 "into a temporary directory and iterate over those files" | Ambiguous build form: file form into a bare temp dir does not work as written and changes file names in assertion messages | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recipe uses `text_only=True` and writes `<status>.md` into `tempfile.TemporaryDirectory()`. Strength: strong |
| PR-003 | MEDIUM | IN-SCOPE | References / self-containment | 7fpc8v E-22..E-25, V-22..V-24 "batch-rule step-2 command"; defined only in `59aiyh` "Batch rule" step 2 | A modest executor must open another plan to find the command and its state path (`.aw/state/59aiyh/`) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OUTCOME-LIST COMMAND defined in this plan with `.aw/state/7fpc8v/`. Strength: strong |
| PR-004 | LOW | IN-SCOPE | Honest documentation | 7fpc8v preamble "Item ids E-01, E-02, E-10 and E-13 are the ids these items had" | Paragraph describes ids this plan does not contain | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to point at `j6o96i`. Strength: strong |
| PR-005 | LOW | UNDER-SCOPE | Execution contract | 7fpc8v gate "Lifecycle transition: the plan moves ... only through `aw ipd finalize`" | Missing "never a hand `git mv`" and conditional runner/hand-executor finalize ownership (`steps/s7-finalize.md`) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added both. Strength: strong |

### Step S5

- Checked: OQ-01 (`Blocking: no`, `Status: resolved`); still accurate (the builder renders through `artifact_meta.render_legacy_text`, `j6o96i` E-01). Findings raised no human-owned question.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | File form or text form for the nine built specs? | Text form (`text_only=True`) written as `<status>.md` into a temporary directory | File form into a fixture repository from `support.init_repo` plus `.aw/` (rejected: changes file names in assertion messages and adds repository setup to three unit tests for no tested behavior) | `j6o96i` E-01 TEXT FORM rule ("`repo_root=None` is allowed for text-only calls"); the three tests read only file text | yes |
| D-2 | Which gate values for the deferred spec? | The fixture's own: `issue`, `https://example.com/issues/1`, "waiting on an upstream decision" | Any other valid `GATE_KINDS` value (rejected: the fixtures are the behavior being preserved) | `tests/fixtures/attnview/specs-valid/deferred.md` | yes |

### Step S6

- Re-read E-22..E-25, V-22..V-25, Required tests and the gate after edits; `grep` for `batch-rule`, `step-2` and `builder recipe` found no stale reference outside the Concern's general wording. No new finding.
- `AW-REVIEW: DONE`
