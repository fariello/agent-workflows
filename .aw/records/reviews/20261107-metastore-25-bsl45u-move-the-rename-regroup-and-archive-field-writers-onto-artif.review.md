# Review findings: ipd bsl45u

- Subject-Id: bsl45u
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Proofreading

Checked `.aw/records/plans/pending/20261107-metastore-25-bsl45u-move-the-rename-regroup-and-archive-field-writers-onto-artif.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Concern`, `Scope`, `Project conventions`, `Deferred` | Bare `id6` references and `module.func` symbols without descriptive labels or `path::Symbol` anchors | Added descriptive names on first mention of referenced records and standardized code citations to `path::Symbol` | `technical-writing.md` Requirement 1 and `steps/p-proofread.md` Section 11.1 |
| `Detailed Implementation Checklist (TODO)` | Stale `PIN-FIRST RULE for every "move" item` paragraph citing nonexistent `D-1 to D-6` | Concise `Close-out outcome-list rule` stating that `1hfmpb`, `fnu6kw`, and `9gy5jk` own the code and test moves while `bsl45u` runs the family close-out and writer audit (`D-2`, `D-4`) | `technical-writing.md` Requirements 5, 8, and 11 (remove stale pre-split instructions) |
| `E-02`, `V-02`, `Findings` | Assumed gitignored `.aw/state/bsl45u/family-before.txt` exists in an isolated lane and cited nonexistent pytest nodeid `tests/test_rename_ledger.py::test_applied_plan_rename_appends_one_record` | Consumes `1hfmpb` `F-03` (`<baseline_sha>`, counts, `sha256` digest) with deterministic `git archive` + `PYTHONPATH="$tmpdir" AW_NO_REEXEC=1` regeneration when absent, and cites `tests/test_rename_ledger.py::CliEmissionTests::test_applied_plan_rename_appends_one_record` | `technical-writing.md` Requirements 5, 6, and 7 (executable, verifiable steps and exact identifiers) |
| `E-03`, `V-03`, `Findings` (`F-04`) | No writer audit across the five family modules despite `Goal` claiming metadata edits go only through `artifact_meta` | Added `E-03` / `V-03` and `F-04` auditing raw writes and `- Set:`/`- Order:`/`- Id:`/`- Status:` bullet literals across all five family modules plus bare `python3 -m pytest` (`4sd62s` AC-1b) | `technical-writing.md` Requirements 5 and 6 (verifiable requirements matching `Goal`) |
| `Proposed changes (ordered, validatable)` | Single-line numbered item with no diagram | Added three-step ordered list and Mermaid `flowchart TD` showing `1hfmpb` -> `fnu6kw` -> `9gy5jk`, isolated-lane baseline regeneration, `E-02`, `E-03` defect branch, `F-04` recording, and downstream unblocking | `technical-writing.md` Requirement 12 (three prerequisite records and branched close-out/audit process) |
| `Validation and cross-check` | Two em dashes on pre-edit line 114 | Replaced both em dashes with commas | Resolve `IPD-C802` advisories |

### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|

### Step T
- Checked: `- Scope-Paths:`, execution-item and task-group counts, spec/contract surface, and cross-plan dependency edges in Set `metastore`.
1. Yes: while `bsl45u` edits no `.spec.md` or Python source, it is the verification gate (`executed:bsl45u`) that downstream `metastore` plans (`b4y4ee`, `xexn45`, `8q27jt`, `9o83cr`, `0xsx2n`, `786w7r`) rely on for `spec 4sd62s` section 7 step 4 completion across the rename, regroup, and archive verb family.
2. No: `- Scope-Paths:` contains only `.aw/records/plans/pending/20261107-metastore-25-bsl45u-move-the-rename-regroup-and-archive-field-writers-onto-artif.ipd.md` and touches no leak-sanitizer, commit-helper, lock, containment, or sandbox code.
3. Cross-cutting across five production modules (`agent_workflows/artifact_rename.py`, `agent_workflows/plans_refs.py`, `agent_workflows/plans_archive.py`, `agent_workflows/research_refs.py`, `agent_workflows/research_archive.py`), four shared cross-module rename test suites, and six prerequisite plans (`tve77h`, `2xwb9b`, `7yr827`, `1hfmpb`, `fnu6kw`, `9gy5jk`).
4. Yes: `- Scope-Paths:` explicitly lists `.aw/records/plans/pending/20261107-metastore-25-bsl45u-move-the-rename-regroup-and-archive-field-writers-onto-artif.ipd.md`.
5. Yes: an unexecutable isolated-lane baseline comparison or a missing writer audit on `plans_archive.py`, `research_refs.py`, and `research_archive.py` (omitted from `xexn45` `E-15`) would either fail `bsl45u` `E-02` at runtime or pass unmigrated metadata writers downstream to `b4y4ee`, `xexn45`, and `9o83cr`.

AW-TIER: complex

### Step R1
- Checked: `agent_workflows/artifact_rename.py`, `agent_workflows/plans_refs.py`, `agent_workflows/plans_archive.py`, `agent_workflows/research_refs.py`, `agent_workflows/research_archive.py`, `agent_workflows/record_history.py`, `agent_workflows/artifact_refs.py`, `tests/test_rename_ledger.py`, `tests/test_rename_group_machine_output.py`, `tests/test_mutation_result_facts.py`, `tests/test_artifact_refs_rewrite.py`, `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md`, and sibling plans `63ib9r`, `xexn45`, `7yr827`, `1hfmpb`, `fnu6kw`, `9gy5jk`, `b4y4ee`, `9o83cr`, `786w7r`, and `qttoyc` at `HEAD` `326d38481`.
- Verified live writer and bullet-literal counts across the five family modules before the moves:
  - `agent_workflows/artifact_rename.py`: 3 `_core.atomic_write` calls (`_update_frontmatter_metadata` x2, `_update_or_inject_set_metadata` x1) and 11 `- Set:`/`- Order:`/`- Id:` bullet literals.
  - `agent_workflows/plans_refs.py`: 1 `_core.atomic_write` call (`apply_renames`) and 4 `- Set:`/`- Order:` bullet literals (`_set_metadata`).
  - `agent_workflows/plans_archive.py`: 0 record-metadata writes and 2 `INDEX.*` `write_text` calls (`apply_shard_moves`).
  - `agent_workflows/research_refs.py`: 1 `_atomic_write` call + `update_frontmatter_fields` (`_apply_renames`, shared by `run_mv` and `run_set_assign`, which also calls `record_history.record_rename`).
  - `agent_workflows/research_archive.py`: 1 `RF._atomic_write` call + `_rewrite_status_in_text` (`apply_moves`) plus 2 `INDEX.*` `write_text` calls (`apply_moves`).
- Empirically ran the four shared rename suites (`60 passed`, sorted outcome digest `a58e0fedfc9185c64dd5418c2c1078a83742f5632791197de2a9ddff672f175b`) and demonstrated that `git archive HEAD agent_workflows tests pyproject.toml | tar -x -C "$tmpdir"` with `(cd "$tmpdir" && PYTHONPATH="$tmpdir" AW_NO_REEXEC=1 python3 -m pytest ...)` imports `$tmpdir/agent_workflows` in both parent and subprocess invocations and reproduces the exact `sha256` digest.
- Identified three `PR-001` gaps (isolated-lane absence of gitignored `.aw/state/bsl45u/family-before.txt`, wrong pytest nodeid omitting `CliEmissionTests::` in `tests/test_rename_ledger.py:221,272`, and missing five-module writer audit covering `plans_archive.py`, `research_refs.py`, and `research_archive.py`) plus stale pre-split `Project conventions`, `Findings`, `Behavior decisions`, `Deferred`, and gate text (`PR-002`).
- Also noted an adjacent Set-level gap outside `bsl45u` scope (`agent_workflows/artifact_refs.py::apply_scope_path_reference_rewrites` rewrites `- Scope-Paths:` directly via `_SCOPE_PATHS_LINE_RE` and `atomic_write`, missed by `786w7r` `LIT`, `xexn45` `E-15`, and `qttoyc` `E-02`); reported in the lane outcome `defect_report` without widening `bsl45u`.

### Step R2
- Checked: `E-*`/`V-*` 1:1 bijection, `- Highest E allocated:`, `- Scope-Paths:`, `- Item-Dependencies:`, evidence verifiability, live-count framing, qualified `4sd62s` citations, and `Approval and execution gate`.
- Allocated `E-03` / `V-03` via `aw ipd sync --apply` (`- Highest E allocated: 03`), verified 1:1 bijection (`E-02` <-> `V-02`, `E-03` <-> `V-03`), confirmed `- Scope-Paths:` matches the single file `bsl45u` edits (its own IPD), and confirmed `- Item-Dependencies:` (`executed:tve77h, executed:2xwb9b, executed:7yr827, executed:1hfmpb, executed:fnu6kw, executed:9gy5jk`) lists every prerequisite.
- Updated `V-02` and `V-03` to demand concrete pasted outputs, digests, exit codes, `F-04` classification, per-writer attestation, and the `python3 -m pytest` summary line (`PR-001`, `PR-002`).

### Step R3
- Checked: command safety, temporary-directory hygiene, file write scope, and trust boundaries in `E-02` and `E-03`.
- `E-02`'s isolated-lane regeneration extracts tracked `agent_workflows`, `tests`, and `pyproject.toml` from `<baseline_sha>` into `mktemp -d`, runs deterministic local `pytest` with `AW_NO_REEXEC=1`, removes `$tmpdir`, and writes only under gitignored `.aw/state/bsl45u/` without creating git worktrees or touching outside checkouts. `E-03` runs read-only `rg` queries and `python3 -m pytest` and fails closed on any unexpected writer or bullet-literal match.

### Step R4
- Checked: correctness, domain invariants, anti-regression coverage, conceptual density, and `Spec / documentation sync`.
- Confirmed `D-2` and `D-4` match reviewed `1hfmpb` (`checkpoint` `"id"` minting, dual-form `prompts` `op == "set"`, pre-batch `dry_run=True`), `fnu6kw` (`_set_metadata` and `apply_renames` pre-pass refusal), and `9gy5jk` (`research` `---` YAML rules and `op: "transition"` status updates).
- Conceptual density check: `E-02` owns the four-module baseline comparison and `D-4` check, and `E-03` owns the five-module writer audit and core test gate (`0` `IPD-Z603` advisories). `Spec / documentation sync` ("None") is truthful because `bsl45u` changes no CLI flags, file formats, or user-facing behavior.

### Step R5
- Checked: all eight reviewer personas against `.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas` (QA/QC, testing/regression, UI/UX, architect, software engineer, power user, novice, stakeholder).
- QA/QC and testing/regression caught the missing `CliEmissionTests::` class qualifier in `tests/test_rename_ledger.py` and the unaudited `plans_archive.py`, `research_refs.py`, and `research_archive.py` modules omitted from `xexn45` `E-15` (`PR-001`); software engineer and power user caught that `.aw/state/bsl45u/family-before.txt` is gitignored across isolated runner lane worktrees and that `python3 -c` / `pytest` needs `cd "$tmpdir"` + `PYTHONPATH="$tmpdir"` + `AW_NO_REEXEC=1` to avoid importing the current lane's `agent_workflows` (`PR-001`); novice caught stale `PIN-FIRST` move instructions and `rg` exit `1` zero-match semantics (`PR-001`, `PR-002`).

### Step R6
- Checked: plan size and decomposition boundaries after the 2026-11-07 and 2026-11-09 splits.
- `bsl45u` already split all code and characterization-test edits into `1hfmpb` (Order 127), `fnu6kw` (Order 128), and `9gy5jk` (Order 129), leaving 2 focused close-out/audit `E-*` items in 1 task group with 0 code `Scope-Paths`. No further split is warranted.

### Step R7
- Checked: cross-plan consistency across orchestrator `63ib9r` (`E-22`, `E-69`, `E-70`, `E-71`), parent `xexn45` (`E-06`, `E-14`, `E-15`), prerequisites `tve77h`, `2xwb9b`, `7yr827`, `1hfmpb` (`E-01`, `F-03`), `fnu6kw`, and `9gy5jk`, and downstream plans `b4y4ee`, `8q27jt`, `9o83cr`, `0xsx2n`, and `786w7r`.
- Connected `bsl45u` `E-02` directly to reviewed `1hfmpb` `F-03`, corrected `research_refs._apply_renames` writer attribution from reviewed `9gy5jk` PR-001, corrected `b4y4ee` carrier attribution for `tests/test_writers_merge_independence.py`, and closed the `xexn45` `E-15` writer-audit gap on `plans_archive.py`, `research_refs.py`, and `research_archive.py` (`PR-001`, `PR-002`).

### Step S5
- Checked: pre-existing open questions (none), review-raised questions, and remediation risk.
- All questions were resolved directly from repository code, live test runs, `spec 4sd62s`, and reviewed sibling plans (`D-1` and `D-2` below, both `Reversible: yes`). Zero `OPEN` or `DEFERRED` findings remain.

### Pass 2
- Re-ran checks P, R1, R2, R4, R7, and S5 against the revised `.aw/records/plans/pending/20261107-metastore-25-bsl45u-move-the-rename-regroup-and-archive-field-writers-onto-artif.ipd.md`.
- Verified both `E-03` `rg` commands and `aw ipd lint --phase author --agent` (`0` findings across all severities) against current `HEAD` `326d38481`, confirmed every reference across `E-02..E-03`, `V-02..V-03`, `F-01..F-04`, `D-2`, `D-4`, `Proposed changes`, `Deferred`, and `Approval and execution gate` is internally consistent, and verified zero em/en dashes, zero `TODO` placeholders, zero absolute paths, and zero `file://` URIs.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PR-001 | high | UNDER-SCOPE | R1 / R2 / R7 | `.aw/records/plans/pending/20261107-metastore-25-bsl45u-move-the-rename-regroup-and-archive-field-writers-onto-artif.ipd.md:30,40,117`, `.aw/records/plans/pending/20261109-metastore-127-1hfmpb-move-the-artifact-rename-field-writers-onto-artifact-meta.ipd.md:43,81`, `tests/test_rename_ledger.py:221,272`, `.aw/records/plans/pending/20261102-metastore-07-xexn45-move-the-remaining-metadata-writers-onto-artifact-meta.ipd.md:54` | `E-02` and `V-02` assumed gitignored `.aw/state/bsl45u/family-before.txt` is present in an isolated runner lane without consuming `1hfmpb` `F-03` (`<baseline_sha>` and `sha256` digest) to regenerate it (`diff` exits `2`), cited nonexistent nodeid `tests/test_rename_ledger.py::test_applied_plan_rename_appends_one_record` (missing `CliEmissionTests::`), and omitted any writer audit across the five family modules even though `Goal` claims metadata edits go only through `artifact_meta` and `xexn45` `E-15` omits `plans_archive.py`, `research_refs.py`, and `research_archive.py` | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Updated `E-02` and `V-02` with `1hfmpb` `F-03` `sha256` verification, demonstrated `git archive <baseline_sha>` + `PYTHONPATH="$tmpdir" AW_NO_REEXEC=1` regeneration, and the `CliEmissionTests::` nodeid, and added `E-03` / `V-03` (`aw ipd sync --apply`) + `F-04` auditing all five family modules plus `python3 -m pytest` (strength: very strong) |
| PR-002 | medium | IN-SCOPE | R1 / R2 / R4 / R7 | `.aw/records/plans/pending/20261107-metastore-25-bsl45u-move-the-rename-regroup-and-archive-field-writers-onto-artif.ipd.md:36,49,51-58,67,72,86-88,127-131` | Stale pre-round-3 prose instructed PIN-FIRST move diffs citing nonexistent `D-1 to D-6`, falsely stated `bsl45u` adds `write_legacy` (owned by `7yr827`), copied unrelated `xexn45` conventions and `D-2` anchor examples (`coverage_record`, `mark_plan_attended`), omitted `research_refs._apply_renames` as a `record_history.record_rename` caller and as the shared research writer (still naming non-writers `run_mv`/`run_set_assign` corrected in `9gy5jk` PR-001), misattributed `b4y4ee`'s merge-independence test to `xexn45`, and lacked explicit prerequisite/audit-defect stop conditions in the gate | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Replaced move boilerplate with a close-out outcome-list note, aligned `Project conventions`, `F-01..F-03`, `D-2`, `D-4`, and `Deferred` with `7yr827`, `1hfmpb`, `fnu6kw`, `9gy5jk`, `b4y4ee`, and `xexn45`, and added narrow prerequisite, `1hfmpb` `F-03`, diff, and audit-defect stop conditions in `Approval and execution gate` (strength: strong) |
| PR-003 | low | IN-SCOPE | Proofreading | `.aw/records/plans/pending/20261107-metastore-25-bsl45u-move-the-rename-regroup-and-archive-field-writers-onto-artif.ipd.md:5-6,75-79,114` | Pre-edit line 114 contained two em dashes (`IPD-C802`), `Proposed changes` lacked a `technical-writing.md` Requirement 12 Mermaid diagram for the three-part prerequisite chain, isolated-lane baseline branch, and audit defect branch, code references used bare `module.func` instead of `path::Symbol`, and first-mention `id6` tokens lacked descriptive labels | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Removed both em dashes (`IPD-C802`), added a Mermaid `flowchart TD` diagram in `Proposed changes`, standardized code citations to `path::Symbol`, and added descriptive labels on first mention of referenced records (strength: strong) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D-1 | How should `bsl45u` `E-02` obtain `.aw/state/bsl45u/family-before.txt` when executed in an isolated runner lane worktree where `1hfmpb`'s gitignored `.aw/state/` directory is absent? | Read `<baseline_sha>` and the `sha256` digest from executed `1hfmpb` `F-03`, regenerate `family-before.txt` via `git archive <baseline_sha> agent_workflows tests pyproject.toml \| tar -x -C "$tmpdir"` and `(cd "$tmpdir" && PYTHONPATH="$tmpdir" AW_NO_REEXEC=1 python3 -m pytest ...)` when absent or mismatched, and verify `sha256sum` matches `1hfmpb` `F-03` before running `diff` | Use `git worktree add` inside the lane (mutates repository worktree state during a read-only close-out) or compare only counts from `1hfmpb` `F-03` without `diff` (loses per-nodeid outcome comparison) | `.aw/records/plans/pending/20261109-metastore-127-1hfmpb-move-the-artifact-rename-field-writers-onto-artifact-meta.ipd.md:43,81` (`E-01`, `F-03`) and live verification at `326d38481` reproducing `sha256` `a58e0fedfc9185c64dd5418c2c1078a83742f5632791197de2a9ddff672f175b` | yes |
| D-2 | Should `bsl45u` allocate a dedicated `E-03` / `V-03` item for the five-module writer audit and `python3 -m pytest` gate rather than folding them into `E-02` or leaving them to `xexn45` `E-15`? | Allocate `E-03` / `V-03` via `aw ipd sync --apply` (with `F-04`) to audit all five family modules (`artifact_rename.py`, `plans_refs.py`, `plans_archive.py`, `research_refs.py`, `research_archive.py`) and run bare `python3 -m pytest` (`4sd62s` AC-1b) | Fold the audit into `E-02` (mixes test-suite baseline comparison with five-module source auditing, violating `IPD-Z603` single-concern sizing) or rely on `xexn45` `E-15` (omits `plans_archive.py`, `research_refs.py`, and `research_archive.py`) | `.aw/records/plans/pending/20261107-metastore-25-bsl45u-move-the-rename-regroup-and-archive-field-writers-onto-artif.ipd.md:30` (`Goal`), `.aw/records/plans/pending/20261102-metastore-07-xexn45-move-the-remaining-metadata-writers-onto-artifact-meta.ipd.md:54` (`E-15`), and `spec 4sd62s` `AC-1b` | yes |
