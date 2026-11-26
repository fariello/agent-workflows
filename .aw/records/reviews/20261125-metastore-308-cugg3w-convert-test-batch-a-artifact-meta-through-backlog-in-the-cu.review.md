# Review findings: ipd cugg3w

- Subject-Id: cugg3w
- Subject-Type: ipd
- Reviewed-At: 2026-11-26
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Step T
- Selected tier: `standard`
- Rationale: Child plan modifying 8 test modules inside the cumulative cutover code patch (`.aw/system/cutover/metastore-code.cutover.patch`), spanning core metadata cache/read/write tests, attention contract tests, mutation verbs, and backlog verbs/validation.

AW-TIER: standard

### Step R1: References, Scope, and Dependencies
- Checked: `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md`, `.aw/records/plans/pending/20261125-metastore-306-89mtbl-switch-the-shared-test-record-builder-and-codemod-to-the-log.ipd.md`, `.aw/records/plans/pending/20261109-metastore-257-x1mmdp-add-the-log-format-test-builder-switch-to-the-cutover-code-p.ipd.md`, `.aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md`, `.aw/system/cutover/metastore-code.cutover.patch`, `tests/test_artifact_meta_cache.py`, `tests/test_artifact_meta_loader_parity.py`, `tests/test_artifact_meta_read.py`, `tests/test_artifact_meta_write.py`, `tests/test_attention_contract.py`, `tests/test_attention_priority_blocker.py`, `tests/test_awcmdsurf_mutation_verbs.py`, `tests/test_backlog.py`, `agent_workflows/backlog.py`, `agent_workflows/artifact_meta.py`, `agent_workflows/check_engine.py`, `agent_workflows/runner_shared.py`, `agent_workflows/attention.py`.
- Found that `Concern` and `F-04` cited gitignored attempt-1 lane evidence absent in fresh lanes (`PR-005`), and `## Deferred / out of scope` omitted `cxxmyv` (`PR-006`).
- Found a major production-code cutover gap in `agent_workflows/backlog.py` (`validate_item`, `run_check`, `item_from_text`, `find_item`, `blocks_release_of_item`, `find_duplicate_candidates`, `run_new` duplicate scan) and its callers (`check_engine.py:1652`, `runner_shared.py:25389, 55957`), which were not made log-aware in `.aw/system/cutover/metastore-code.cutover.patch` and therefore cause `tests/test_backlog.py` (7+ tests) to fail on conformant post-cutover backlog items (`PR-001`).

### Step R2: Executability and Verification Rigor
- Checked: Every test function across all 8 batch A modules against the post-cutover `artifact_meta.py`, `backlog.py`, `set_records.py`, `status_set.py`, `plans_refs.py`, `artifact_rename.py`, and `attention.py` hunks in `.aw/system/cutover/metastore-code.cutover.patch`, plus `89mtbl` F-02's `text_only=True` and `raw_fields` contracts.
- Probed `agent_workflows.backlog.validate_item` directly against `artifact_meta.render_in_file_mirror("abc123", "backlog", "open")`, confirming 5 false-positive errors (`backlog.priority-invalid`, `backlog.kind-invalid`, `backlog.set-missing`, `backlog.summary-missing`, `backlog.history-empty`) on a conformant post-cutover backlog item (`PR-001`).
- Verified `tests/test_artifact_meta_write.py` already uses the log format; its sole failure is `test_append_dry_run` calling `artifact_meta.append` directly with `op: "create"` on a nonexistent log without `_from_create=True` (`PR-002`).
- Verified 8 of 11 failing tests across `test_artifact_meta_cache.py`, `test_artifact_meta_loader_parity.py`, and `test_artifact_meta_read.py` test removed Phase-B unlogged-Markdown cache loading or `read_at` Markdown fallback rather than convertible bullet fixtures (`PR-003`).
- Verified second-half traps in `test_attention_contract.py` (`spec_status_bullet` / `extract_newest_history_entry` with `text_only=True`), `test_attention_priority_blocker.py` (`raw_fields` + `text_only=True`), `test_awcmdsurf_mutation_verbs.py` (`setUp` writing `text_only=True` without a log), and `test_backlog.py` (4 direct calls to removed `backlog._render_item` plus inline-history and `read_text` assertions) (`PR-004`).
- Verified `V-02` and `V-03` omitted an exact `rg` pattern (`PR-005`), and `E-01`, `V-05`, and `## Approval and execution gate` omitted exact patch paths, `git status --short` verification, and conditional runner-lane vs. hand-run `aw ipd finalize` ownership (`PR-006`).

### Step R3: Security, Isolation, and Safety
- Checked: Scratch worktree containment (`.aw/state/cugg3w/scratch`), live-tree safety, `- Scope-Paths:` fence, `aw commit cugg3w` path-scoped commit contract, never-push rule, and no test-assertion weakening rule.
- Verified no security or secret-leak risks; added explicit `git status --short` check in `E-05`/`V-05` to prove no live edits escape `- Scope-Paths:`.

### Step R4: Engineering Quality and Contract Conformance
- Checked: Technical writing standard (`.aw/system/workflows/technical-writing/technical-writing.md`), `IPD-Z603` unit-sizing hygiene, `E-*`/`V-*` bijection, Mermaid diagram validity, and `check.review-finding-unescalated` / `MD-9` open-question rules.
- Confirmed `PR-001` is properly escalated into `OQ-01` carrying `- Blocking: yes`, `- Status: open`, `- Owner: maintainer`, `- Finding: PR-001`, and a strength-labeled recommendation (`strength: strong`).

### Step S5: Open Questions and Decisions
- Checked: Collected all 6 findings; resolved `PR-002` through `PR-006` from repository evidence (all `Overall:Low`, `Reversible: yes`, recorded in `### Decisions` `D-1..D-5`).
- Escalated `PR-001` (`Overall:Medium-High`) as blocking human-owned question `OQ-01` in the plan and as `backlog-log-aware-gap` (`gates_verdict: true`) in `.aw/state/lane-submissions/run-20261126T020242Z-3080634/04-cugg3w/attempt-1/outcomes/04-cugg3w.json` because adding production-code fixes to `agent_workflows/backlog.py`, `check_engine.py`, and `runner_shared.py` inside a test-only conversion batch changes plan scope and sequencing across 14 backlog test modules.

### Pass 2: Verification of Edits
- Re-read the revised plan `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md` from top to bottom.
- Verified `PR-002` through `PR-006` are fully applied, `PR-001` is escalated to `OQ-01` with `- Blocking: yes` and `- Finding: PR-001`, `- Review-Depth: standard` and `- Readiness: no-go` are present, `## Workflow history` leads with the `REVIEWED - OPEN QUESTIONS` entry, `E-01..E-05` match `V-01..V-05` 1:1, and the Mermaid diagram matches the ordered steps.

### Findings
| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | repo-wide | Production cutover readiness (`backlog.py`) | `.aw/system/cutover/metastore-code.cutover.patch`; `agent_workflows/backlog.py:332,397,650,675,945,1614`; `agent_workflows/check_engine.py:1652`; `agent_workflows/runner_shared.py:25389,55957`; `tests/test_backlog.py:82` | `backlog.run_new` creates log-format backlog records carrying only the 2-field YAML mirror (`id`, `status`) in `.backlog.md`, but `backlog.validate_item`, `backlog.run_check`, and `item_from_text` callers were never made log-aware in `.aw/system/cutover/metastore-code.cutover.patch`. Direct probe confirms `validate_item` emits 5 false-positive errors on a conformant post-cutover backlog item, blocking `tests/test_backlog.py` (and 13 sibling `tests/test_backlog_*.py` modules) from passing without production edits in the code patch. | C:Medium-High; U:Medium; S:Low; F:High; Overall:Medium-High | OPEN | Escalated to maintainer as `OQ-01` (`- Blocking: yes`, `- Finding: PR-001`) and parked in outcome JSON (`gates_verdict: true`) to decide between a dedicated production-fix child plan ahead of `cugg3w` (Recommended, `strong`), expanding `cugg3w` scope, or deferring `tests/test_backlog.py`. |
| PR-002 | BLOCKER | plan-local | E-02 (`test_artifact_meta_write.py`) | `tests/test_artifact_meta_write.py:90-118`; `.aw/system/cutover/metastore-code.cutover.patch` (`artifact_meta.append` hunk `@@ -9205,6 +6387,11 @@`) | `tests/test_artifact_meta_write.py` already uses the log format; its sole failing test (`test_append_dry_run`) calls `artifact_meta.append("dry001", [{"op": "create", ...}], dry_run=True)` on a nonexistent log without `_from_create=True`, which post-cutover `artifact_meta.append` now explicitly refuses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-02` item 4 to specify testing `artifact_meta.create(..., dry_run=True)` and/or `artifact_meta.append(..., [{"op": "note", ...}], dry_run=True)` on an existing record (`D-1`). |
| PR-003 | BLOCKER | plan-local | E-02 (`test_artifact_meta_cache.py`, `test_artifact_meta_loader_parity.py`, `test_artifact_meta_read.py`) | `tests/test_artifact_meta_cache.py:400,460`; `tests/test_artifact_meta_loader_parity.py:1-152`; `tests/test_artifact_meta_read.py:220-248,548-611`; `.aw/system/cutover/metastore-code.cutover.patch` (`_load_sources`, `read_at` hunks) | 8 of 11 failing tests across these three modules explicitly test removed Phase-B unlogged-Markdown cache loading or `read_at` Markdown fallback rather than convertible bullet fixtures, and `test_query_filters` writes a legacy bullet `.review.md` instead of an `op: "review"` event per spec `4sd62s` Section 4.1a. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-02` items 1 to 3 with exact per-test log-conversion, `m0001` repoint, and rule-4 retirement instructions citing spec `4sd62s` Sections 4.1a, 4.3, 4.4, 4.6, 5.2, and 5.3 (`D-2`). |
| PR-004 | HIGH | plan-local | E-03 (second half of batch A) | `tests/test_attention_contract.py:245,298,490-645`; `tests/test_attention_priority_blocker.py:130,188,265`; `tests/test_awcmdsurf_mutation_verbs.py:39-50`; `tests/test_backlog.py:122-1984` | `E-03` omitted `89mtbl` F-02 `text_only=True`/`raw_fields` interactions in `test_attention_contract.py` (`spec_status_bullet`, `extract_newest_history_entry`) and `test_attention_priority_blocker.py`, `test_awcmdsurf_mutation_verbs.py::setUp` writing a `text_only=True` plan with no log, and `test_backlog.py`'s 4 direct calls to removed `backlog._render_item` plus inline-history/`read_text` assertions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-03` items 1 to 4 with concrete per-module conversion rules (`D-3`). |
| PR-005 | HIGH | plan-local | Provenance & verification (`Concern`, `F-04`, `V-02`, `V-03`) | `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md:5,82,132,136` | `Concern` and `F-04` cited gitignored attempt-1 lane evidence absent in isolated lanes; `V-02` and `V-03` required `rg` for removed symbols without specifying the exact pattern or exit code 1 expectation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Marked attempt-1 counts as historical provenance (starting execution from `89mtbl` F-04) and specified the exact removed-symbol `rg` command and exit-1 expectation in `V-02` and `V-03` (`D-4`). |
| PR-006 | MEDIUM | plan-local | Execution gate & hygiene (`E-01`, `E-05`, `V-05`, `Deferred`, `Approval gate`) | `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md:38,62,99-105,144,153` | `## Approval and execution gate` unconditionally instructed `aw ipd finalize` instead of distinguishing managed runner lanes from hand-run sessions; `E-01` omitted exact patch paths; `V-05` omitted `git status --short` clean-tree verification; `## Deferred / out of scope` omitted `cxxmyv`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-01`, `E-05`, `V-05`, `## Deferred / out of scope`, and `## Approval and execution gate` (`D-5`). |

### Proofreading
#### Changes
| Location | Original | Revised | Rule |
|---|---|---|---|
| `Concern` & `F-04` | Cited gitignored `.aw/state/lane-submissions/.../failing-modules.txt` as live evidence | Attributed attempt-1 counts as historical `x1mmdp` provenance; anchored execution to `89mtbl` F-04 | Accuracy & self-contained provenance |
| `E-01` & `E-05` | Generic `"the docs patch"` / `"the code patch"` / `"<this plan>"` | Named exact repo-relative patch and plan paths | Precision & executability |
| `V-02` & `V-03` | Unspecified `"rg for the removed symbols"` | Exact `rg -n '...' <modules>` command with exit 1 and empty stdout | Testable verification |

#### Issues
| Location | Issue | Severity | Action |
|---|---|---|---|
| `## Open questions` (`OQ-01`) | Blocking scope/sequencing decision on unpatched `agent_workflows/backlog.py` | BLOCKER | Escalated to maintainer (`gates_verdict: true`) |

### Decisions
| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `tests/test_artifact_meta_write.py::test_append_dry_run` be updated for the post-cutover `artifact_meta.append` contract? | Update `test_append_dry_run` to test `artifact_meta.create(..., dry_run=True)` for creation dry-run and/or `artifact_meta.append(..., [{"op": "note", ...}], dry_run=True)` on an already-created record. | Leave `test_append_dry_run` calling `meta.append` with `op: "create"` on a nonexistent log (rejected: post-cutover `artifact_meta.append` explicitly refuses missing logs without `_from_create=True`). | `tests/test_artifact_meta_write.py:90-118`, `.aw/system/cutover/metastore-code.cutover.patch` (`artifact_meta.py` `@@ -9205,6 +6387,11 @@`). | yes |
| D-2 | How should Phase-B legacy cache-loader and `read_at` tests in `test_artifact_meta_cache.py`, `test_artifact_meta_loader_parity.py`, and `test_artifact_meta_read.py` be handled? | Distinguish removed Phase-B behavior (retire under rule 4 citing spec `4sd62s` 4.3/4.4/4.6/5.2/5.3, or repoint legacy-subject tests to `m0001_metadata_v2.load_legacy_artifact` under rule 3) from surviving log-cache tests (seed in log format and use `op: "review"` for `test_query_filters`). | Treat all 11 failing tests as uniform bullet-fixture conversions to `RecordBuilder` (rejected: would either fail on removed `read_at`/orphan behavior or make legacy-loader test names false). | `tests/test_artifact_meta_cache.py:400,460`, `tests/test_artifact_meta_loader_parity.py:1-152`, `tests/test_artifact_meta_read.py:220-248,548-611`, `.aw/system/cutover/metastore-code.cutover.patch`. | yes |
| D-3 | How should `E-03` address `text_only=True` / `raw_fields` interactions and removed `backlog._render_item` calls in the second half of batch A? | Explicitly specify `RecordBuilder(root)` log materialization for disk-backed tests, explicit text or rule-4 handling for `spec_status_bullet`/`extract_newest_history_entry`, `artifact_meta.read`/`history`/`assert_field` for backlog state/history checks, and rule-1/rule-4 handling for the 4 removed `backlog._render_item` calls. | Leave `E-03` as a bare list of 4 filenames and attempt-1 counts (rejected: hides concrete `89mtbl` F-02 and removed-API traps). | `tests/test_attention_contract.py:245,298,490-645`, `tests/test_attention_priority_blocker.py:130,188,265`, `tests/test_awcmdsurf_mutation_verbs.py:39-50`, `tests/test_backlog.py:122-1984`. | yes |
| D-4 | How should `Concern`, `F-04`, `V-02`, and `V-03` cite attempt-1 census counts and removed-symbol `rg` checks? | Attribute attempt-1 counts as historical `x1mmdp` provenance (anchoring execution to `89mtbl` F-04) and specify the exact `rg -n` removed-symbol pattern and exit-1 expectation in `V-02` and `V-03`. | Keep direct citations to gitignored lane-submission files and vague `rg` instructions (rejected: file is absent in fresh lanes and vague `rg` can miss `_render_item` or `load_legacy_artifact`). | `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md:5,82,132,136`. | yes |
| D-5 | How should `E-01`, `E-05`, `V-05`, `## Deferred / out of scope`, and `## Approval and execution gate` align with the runner-lane execution contract? | Name exact patch/plan paths in `E-01`/`E-05`, add `git status --short` verification in `V-05`, list `cxxmyv` in `## Deferred / out of scope`, and distinguish managed runner lanes from hand-run sessions for `aw ipd finalize`. | Keep unconditional `aw ipd finalize` instruction and generic patch references (rejected: violates `s7-finalize.md` runner-lane ownership rule). | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-36`, `.aw/records/plans/pending/20261125-metastore-306-89mtbl-switch-the-shared-test-record-builder-and-codemod-to-the-log.ipd.md`. | yes |

## Round 2

### Step T
- Selected tier: `standard`
- Rationale: Re-review of child plan `cugg3w` after the maintainer answered blocking question `04-cugg3w-a1-backlog-log-aware-gap` (`OQ-01`) with "Split out a dedicated production-fix child plan ahead of cugg3w (Recommended)", authoring Order 314 (`fljn9b`) and updating `cugg3w`'s dependency chain.

AW-TIER: standard

### Step R1: References, Scope, and Dependencies
- Checked: `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md`, `.aw/records/plans/pending/20261125-metastore-314-fljn9b-make-backlog-validation-and-readers-log-aware-in-the-cutover.ipd.md`, `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md`, `.aw/records/plans/pending/20261109-metastore-257-x1mmdp-add-the-log-format-test-builder-switch-to-the-cutover-code-p.ipd.md`, `.aw/records/backlog/graduated/20261125-metastore-01-ldfefd-cutover-tests-unowned.backlog.md`, `agent_workflows/backlog.py`, `agent_workflows/check_engine.py`, `agent_workflows/runner_shared.py`, `agent_workflows/set_records.py`, `agent_workflows/specs.py`, and `.aw/system/cutover/metastore-code.cutover.patch`.
- Verified `fljn9b` (Order 314) chains directly after `nv3upa` (`- Item-Dependencies: executed:nv3upa`) and ahead of `cugg3w` (`- Item-Dependencies: executed:fljn9b`), preserving the serial cumulative code-patch chain (`hdwqex` -> `89mtbl` -> `nv3upa` -> `fljn9b` -> `cugg3w` -> `psm9ac` -> `x8id25` -> `e0g2gt` -> `qi0kl6` -> `x3mig6` -> `x1mmdp`).
- Verified `fljn9b` is wired into orchestrator `63ib9r` (`Highest E allocated: 226`, `E-226`/`V-226`, `## Child IPDs` Order 314, `E-220`/`E-179`/`E-13` dependencies) and into `x1mmdp` (`- Item-Dependencies:` and `## Deferred / out of scope`).
- Swept every stale reference to open `OQ-01` / `PR-001` across `cugg3w` (`Concern`, `Scope`, `Item-Dependencies`, `E-03` item 4, Step 0, `F-05`, `Proposed changes`, `Deferred / out of scope`, `Scope check`, `OQ-01`, `Approval and execution gate`).

### Step R2: Executability and Verification Rigor
- Checked: `E-01` through `E-05` and `V-01` through `V-05` in `cugg3w` after `OQ-01` resolution, plus `E-01` through `E-05` and `V-01` through `V-05` in `fljn9b`.
- Verified `cugg3w` requires zero production edits outside the scratch worktree and has no remaining unblocked dependency on `agent_workflows/backlog.py` because `fljn9b` lands log-aware validation (`validate_item_state`, `validate_item`, `run_check`), readers (`existing_backlog_ids`, `blocks_release_of_item`, `find_item`, `find_duplicate_candidates`, `run_new` duplicate scan), and callers (`check_engine.check_content`, `runner_shared.enforce_freeze_time_refusal` cache key, `runner_shared.perform_coordinator_proposal_file` companion log recovery, `set_records`) before `cugg3w` executes.

### Step R3: Security, Isolation, and Safety
- Checked: Scratch worktree containment, `- Scope-Paths:` fences, `aw commit` path-scoped commit contracts, and never-push clauses in both `cugg3w` and `fljn9b`.
- Verified no security, secret-leak, or live-tree safety issues remain.

### Step R4: Engineering Quality and Contract Conformance
- Checked: Technical writing standard (`.aw/system/workflows/technical-writing/technical-writing.md`), `IPD-Z603` sizing, `E-*`/`V-*` bijection, Mermaid diagrams, and `check.review-finding-unescalated` / `IPD-Q501` gates.
- Verified `PR-001` is cleared (`FIXED`), `OQ-01` carries `- Status: resolved` and `- Owner: maintainer` citing the maintainer's 2026-11-26 answer, `- Readiness: go-pending-approval` is written in `cugg3w`, and `fljn9b` is authored review-ready (`Status: to-review`) with zero `TODO` placeholders.

### Step S5: Open Questions and Decisions
- Checked: `OQ-01` (`PR-001`) resolved by the maintainer's answer to `run-20261126T020242Z-3080634` question `04-cugg3w-a1-backlog-log-aware-gap`; recorded chaining decision `D-1` below (`Reversible: yes`). No open questions remain; wrote empty `questions: []` to `.aw/state/lane-submissions/run-20261126T020242Z-3080634/04-cugg3w/attempt-2/outcomes/04-cugg3w.json`.

### Pass 2: Verification of Edits
- Re-read `cugg3w` and `fljn9b` in full and verified `aw ipd lint --phase review-finalize` on `cugg3w`, `aw ipd lint --phase author` on `fljn9b`, `63ib9r`, and `x1mmdp`, and `check_review_lane_artifacts` conformance on all modified records.

### Findings
| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | repo-wide | Production cutover readiness (`backlog.py`) | `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md` (`OQ-01`, `F-05`); `.aw/records/plans/pending/20261125-metastore-314-fljn9b-make-backlog-validation-and-readers-log-aware-in-the-cutover.ipd.md` | Unpatched `agent_workflows/backlog.py` log-awareness gap blocking `tests/test_backlog.py` and 13 sibling `tests/test_backlog_*.py` modules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Maintainer answered `04-cugg3w-a1-backlog-log-aware-gap` (`OQ-01`, 2026-11-26) with "Split out a dedicated production-fix child plan ahead of cugg3w (Recommended)". Authored Order 314 child plan `fljn9b` chained after `nv3upa`, wired `fljn9b` into `63ib9r` and `x1mmdp`, set `cugg3w`'s `- Item-Dependencies:` to `executed:fljn9b`, marked `OQ-01` resolved, and cleared stale `OQ-01`/`PR-001` references across `cugg3w`. |

### Proofreading
#### Changes
| Location | Original | Revised | Rule |
|---|---|---|---|
| `cugg3w` (`Concern`, `Scope`, `E-03` item 4, `F-05`, `Proposed changes`, `Scope check`, `Approval and execution gate`) | Described `OQ-01` / `PR-001` as open and gating `tests/test_backlog.py` | Updated all references to point to resolved `OQ-01` and prerequisite Order 314 (`fljn9b`) in `- Item-Dependencies:` | Consistency & stale-wording sweep |
| `cugg3w` (`## Deferred / out of scope`) | Did not list `fljn9b` | Added `fljn9b` carrier for `backlog.py` and caller log-awareness | Explicit scope boundary |

#### Issues
| Location | Issue | Severity | Action |
|---|---|---|---|
| (none) | No unresolved proofreading issues remain. | LOW | None |

### Decisions
| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where in the serial cutover code-patch chain should the new Order 314 child plan (`fljn9b`) sit? | Chain `fljn9b` immediately after `nv3upa` (`- Item-Dependencies: executed:nv3upa`) and set `cugg3w` to `- Item-Dependencies: executed:fljn9b` (wiring `fljn9b` into `63ib9r` and `x1mmdp`). | Chain `fljn9b` right after `hdwqex` before `89mtbl` (rejected: would require editing already-reviewed `89mtbl` and running `fljn9b` before `tests/record_builder.py` is switched to log format). | Maintainer answer to `04-cugg3w-a1-backlog-log-aware-gap` ("Split out a dedicated production-fix child plan ahead of cugg3w (Recommended)"); `.aw/records/plans/pending/20261125-metastore-307-nv3upa-retire-or-repoint-the-legacy-loader-and-writer-unit-tests-in.ipd.md`; `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md`. | yes |

## Round 3

This re-review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261126T161303Z-1366371`) after `cugg3w` was demoted `reviewed -> to-review` for `[stale-review]`. The target plan `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings). The re-review statically re-verified all eight batch A test modules (`tests/test_artifact_meta_cache.py`, `tests/test_artifact_meta_loader_parity.py`, `tests/test_artifact_meta_read.py`, `tests/test_artifact_meta_write.py`, `tests/test_attention_contract.py`, `tests/test_attention_priority_blocker.py`, `tests/test_awcmdsurf_mutation_verbs.py`, `tests/test_backlog.py`), prerequisite `fljn9b`, `nv3upa`, `89mtbl`, `x1mmdp`, `3e0vfy`, and `.aw/system/cutover/metastore-code.cutover.patch` (`artifact_meta.py`, `attention.py`, `attention_contract.py`, `artifact_rename.py`, `backlog.py`, `status_set.py`). It uncovered one `HIGH`, two `MEDIUM`, and one `LOW` findings (`PR-007..PR-010`), all `Overall:Low` remediation risk and all fixed in place. No production code or test code was modified.

### Step T

1. No direct public-interface or spec change (edits 8 test modules only inside `.aw/system/cutover/metastore-code.cutover.patch`), though all downstream children (`szykgd`, `psm9ac`..`x3mig6`, `x1mmdp`) depend on `executed:cugg3w` and the regenerated cumulative patch.
2. No; it does not touch private-data sanitizers, commit/lock helpers, worktree isolation, merge-to-main gates, or host sandbox profiles.
3. No; bounded to 5 execution items across 3 task groups, focused on one cohesive concern (converting the 8 batch A test modules inside the inert code patch).
4. Yes; `- Scope-Paths:` declares both tracked files modified by this plan (the plan file itself and `.aw/system/cutover/metastore-code.cutover.patch`).
5. Yes; misconverting `tests/test_attention_contract.py`, `tests/test_attention_priority_blocker.py`, `tests/test_awcmdsurf_mutation_verbs.py`, or `tests/test_backlog.py` could create vacuous readiness assertions, trigger `validate_id6` / `.agents/` layout failures, or drop backlog validation coverage.

AW-TIER: standard

### Step R1

- Checked: all 8 batch A test modules, `.aw/system/cutover/metastore-code.cutover.patch` (`artifact_meta.py`, `attention.py`, `attention_contract.py`, `artifact_rename.py`, `plans_refs.py`, `backlog.py`, `status_set.py`), `agent_workflows/status_set.py::inventory_all_artifacts`, and `Set: metastore` siblings `nv3upa`, `fljn9b`, `89mtbl`, `3e0vfy`, and `x1mmdp`.
- Found:
  - `tests/test_attention_contract.py::TrackedTreeReachabilityTests._FIXTURES` (lines 490-543) builds class-level `text_only=True` fixtures using invalid short IDs (`s1`, `p1`, `r1`, `b1`, `rel1`, `prm1`) and invalid `Kind: primary`, and `ReleaseRecordsReachTheViewTests._scan_synth` (line 619) uses 5-char `f"relr{status[0]}"`. Post-cutover `artifact_meta.validate_id6` rejects all of these when materialized through `RecordBuilder(root)` (`PR-007`).
  - `tests/test_awcmdsurf_mutation_verbs.py::MutationVerbsTests.setUp` (lines 39-55) writes to `.agents/plans/pending/` with `set="demo (demo)"` and `text_only=True`; switching to `RecordBuilder(self.root)` writes under `.aw/records/plans/pending/` and requires updating `self.pend`, `set="demo"`, `order=1`, and `slug="original"` so `self.doc_b`'s citation and `self.pend.glob` match (`PR-008`).
  - `tests/test_attention_priority_blocker.py::ReadinessReaderTests.test_agrees_with_the_schema_authority` (line 265) can pass vacuously if `RecordBuilder().plan(raw_fields={"Readiness": value}, text_only=True)` produces YAML-only front matter where both readers return `None`; and `tests/test_backlog.py` has 6 `test_validate_item_release_exempt_findings` cases writing `text_only=True` without companion logs, companion `text_only=True` release/carrier-plan fixtures (lines 862, 1273), and inline history assertions in `test_release_exempt_setter_roundtrip_and_parity` (lines 1947-1983) (`PR-009`).
  - Confirmed `status_set.inventory_all_artifacts`, `artifact_rename.run_rename_generic` / `run_group_generic`, `artifact_meta.spec_status_bullet`, and `fljn9b`'s backlog validation/reader fixes cover every production dependency of batch A without any new production cutover gap.

### Step R2

- Checked: E/V bijection (`5/5`: `E-01..E-05` to `V-01..V-05`, `- Highest E allocated: 05`), `- Scope-Paths:` (2 tracked paths), `- Item-Dependencies: executed:fljn9b` (matching `63ib9r` row 308), `OQ-01` (`- Status: resolved`, `- Owner: maintainer`, `- Carrier: fljn9b`), concrete `V-*` evidence, re-derivation convention, `rg` coverage, durable carriers (`fljn9b`, `psm9ac`, `x1mmdp`, `cxxmyv`), and `## Approval and execution gate`.
- Found: `V-05` hardcoded a collected test count (`with all 3 tests PASSED`), `V-02`/`V-03` `rg` patterns omitted `append_legacy|restore_legacy_snapshot|LEGACY_LOADER_VERSION|meta\.load_legacy_artifact|meta\.derive_id6`, Step 0 omitted the post-split prerequisite production-fix children from the chain summary, and the Mermaid diagram omitted the `E-01` patch-rejection stop branch (`PR-010`). Also aligned `E-02` item 4 with `nv3upa` Round 2 (`nv3upa` migrates AC-14a/AC-15/writer-leak tests into `tests/test_artifact_meta_write.py` while leaving `test_append_dry_run` for `cugg3w`). All fixed in place.

### Step R3

- Checked (full form, `standard` tier):
  - Security/anti-regression preservation: fixing `ReadinessReaderTests.test_agrees_with_the_schema_authority` prevents vacuous readiness-parser agreement (`PR-009`), and verifying `tests/test_artifact_meta_write.py` unfiltered in `E-02`/`V-02` exercises both `test_append_dry_run` and every AC-14a/AC-15/writer-leak test migrated by `nv3upa`.
  - Workspace containment: edits occur strictly inside gitignored `.aw/state/cugg3w/scratch`, removed before commit; no live code, secrets, or outbound calls are touched.

### Step R4

- Checked: correctness, anti-regression, testing/verification, KISS, right-sizing/conceptual density per E-item, and `## Spec / documentation sync`.
- Found `PR-007..PR-010` (all `Overall:Low`, all fixed in place). Right-sizing check: 5 E-items across 3 task groups, 1 work `Scope-Path` (`.aw/system/cutover/metastore-code.cutover.patch`), 4 modules per conversion step (`E-02`, `E-03`) with explicit per-module rules. No split needed.

### Step S5

- Checked: `## Open questions` (`OQ-01` resolved by maintainer 2026-11-26; no open questions remain). All four Round 3 findings (`PR-007..PR-010`) have `Overall:Low` remediation risk and are settled by authoritative repository evidence. Two reversible review decisions are recorded in `### Decisions` (`D-1..D-2`). Outcome JSON records `{"questions": []}`.

### Pass 2

- Re-checked the complete revised plan: front matter (`- Status: reviewed`, `- Review-Depth: standard`, `- Readiness: go-pending-approval`), `## Workflow history`, `## Goal`, `E-01..E-05`, `## Project conventions discovered (Step 0)`, `## Findings` (`F-01..F-05`), `## Proposed changes` and updated Mermaid `flowchart TD`, `## Deferred / out of scope`, `## Scope check`, `## Required tests / validation`, `## Spec / documentation sync`, `## Open questions` (`OQ-01` resolved), `V-01..V-05`, and `## Approval and execution gate`.
- Verified `5/5` E/V bijection, unchanged `- Scope-Paths:` and `- Item-Dependencies: executed:fljn9b`, zero bare `file:line` citations, zero em/en dashes, and clean `aw ipd lint --phase review-finalize --agent`.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-007 | HIGH | IN-SCOPE | R1 / R4 / `E-03` (`test_attention_contract.py`) invalid short IDs and class-level `_FIXTURES` | `tests/test_attention_contract.py::TrackedTreeReachabilityTests._FIXTURES` (lines 490-543: `s1`, `p1`, `r1`, `b1`, `rel1`, `prm1`, `Kind: primary`); `tests/test_attention_contract.py::ReleaseRecordsReachTheViewTests._scan_synth` (line 619: `f"relr{status[0]}"`); `agent_workflows/artifact_meta.py::validate_id6` | `E-03` item 1 instructed materializing `TrackedTreeReachabilityTests` and `ReleaseRecordsReachTheViewTests` via `RecordBuilder(root)` without noting that `_FIXTURES` is built at class-definition time with `text_only=True` and uses non-6-char IDs (`s1`..`prm1`, `Kind: primary`) and `_scan_synth` uses 5-char `relr{status[0]}`, all of which `artifact_meta.validate_id6` rejects on `artifact_meta.create`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-03` item 1 to materialize those fixtures inside each test via `RecordBuilder(root)` using valid 6-character base36 `id6` values (`sp0001`..`pr0001`, `f"relr0{status[0]}"`) and valid `plan_role="child"` (`D-1`). Recommendation strength: very strong. |
| PR-008 | MEDIUM | IN-SCOPE | R1 / R4 / `E-03` (`test_awcmdsurf_mutation_verbs.py`) `.agents/` layout and parenthetical `set` | `tests/test_awcmdsurf_mutation_verbs.py::MutationVerbsTests.setUp` (lines 39-55: `.agents/plans/pending/`, `set="demo (demo)"`, `self.pend`) | `MutationVerbsTests.setUp` writes to `.agents/plans/pending/` with `set="demo (demo)"`. Materializing via `RecordBuilder(self.root)` writes to `.aw/records/plans/pending/` and rejects parenthetical `set`, so `self.pend` and `set`/`order`/`slug` must be updated together for `self.pend.glob` and `self.doc_b`'s citation to match. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-03` item 3 to specify updating `self.pend = self.root / ".aw" / "records" / "plans" / "pending"`, `set="demo"`, `order=1`, and `slug="original"` alongside `RecordBuilder(self.root)` (`D-1`). Recommendation strength: very strong. |
| PR-009 | MEDIUM | IN-SCOPE | R1 / R3 / R4 / `E-03` vacuous readiness check and `test_backlog.py` release-exempt/companion traps | `tests/test_attention_priority_blocker.py::ReadinessReaderTests.test_agrees_with_the_schema_authority` (line 265); `tests/test_backlog.py::test_validate_item_release_exempt_findings` (lines 1696-1810), lines 862, 1273, `test_release_exempt_setter_roundtrip_and_parity` (lines 1881-1984) | `test_agrees_with_the_schema_authority` becomes vacuous (both readers returning `None`) if log-format `text_only=True` omits `- Readiness:`; and `test_backlog.py` has 6 `test_validate_item_release_exempt_findings` cases writing `text_only=True` without logs, companion release/carrier-plan `text_only=True` fixtures, and inline history checks in `test_release_exempt_setter_roundtrip_and_parity`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-03` items 2 and 4 to require explicit `- Readiness:` text for non-vacuous readiness comparison, log-backed materialization for `test_validate_item_release_exempt_findings` and companion release/carrier-plan fixtures, and `artifact_meta.history` assertions for `test_release_exempt_setter_roundtrip_and_parity` (`D-2`). Recommendation strength: very strong. |
| PR-010 | LOW | IN-SCOPE | R2 / Check P / `V-05` test count, `V-02`/`V-03` `rg` pattern, chain note, and Mermaid stop branch | plan `V-05` (`with all 3 tests PASSED`), `V-02`/`V-03` `rg` regex, Step 0 chain, Mermaid flowchart, `E-02` item 4; `.aw/system/workflows/plan-review/steps/r2-executability.md`; `.aw/system/workflows/technical-writing/technical-writing.md` requirement 12(b)/(d) | `V-05` hardcoded a collected test count (`all 3 tests PASSED`); `V-02`/`V-03` `rg` patterns omitted `append_legacy`, `restore_legacy_snapshot`, `LEGACY_LOADER_VERSION`, `meta\.load_legacy_artifact`, and `meta\.derive_id6`; Step 0 omitted the split production-fix children from the serial chain; `E-02` item 4 did not note `nv3upa`'s migrated tests in `test_artifact_meta_write.py`; and the Mermaid diagram omitted the `E-01` stop branch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced `with all 3 tests PASSED` in `V-05` with pinned guard-test behaviors, expanded `V-02`/`V-03` `rg` patterns, updated Step 0's serial chain and `E-02` item 4 (`nv3upa` handoff note), and added the `Patches apply cleanly?` stop branch to the Mermaid flowchart. Recommendation strength: strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `E-02` item 4 | Mentioned only updating `test_append_dry_run` | Noted `nv3upa` E-03's migrated tests in `tests/test_artifact_meta_write.py` and required running the whole module unfiltered | PR-010 |
| `E-03` items 1 to 4 | Omitted invalid short IDs in `test_attention_contract.py`, `.agents/`/`set` details in `test_awcmdsurf_mutation_verbs.py`, vacuous readiness risk, and `test_backlog.py` release-exempt/companion traps | Added exact per-fixture conversion instructions across all four second-half modules | PR-007, PR-008, PR-009 |
| Step 0, Mermaid diagram, `V-02`, `V-03`, `V-05` | Short chain list, linear Mermaid diagram, narrower `rg` regex, hardcoded `all 3 tests PASSED` | Complete post-split serial chain, E-01 stop branch in Mermaid diagram, expanded removed-symbol `rg` regex, and behavioral guard-test check in `V-05` | PR-010 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `tests/test_attention_contract.py` and `tests/test_awcmdsurf_mutation_verbs.py` fixtures be adapted for `RecordBuilder(root)`? | Materialize `TrackedTreeReachabilityTests` and `ReleaseRecordsReachTheViewTests` inside each test using valid 6-character base36 `id6` values (`sp0001`..`pr0001`, `f"relr0{status[0]}"`) and `plan_role="child"`, and update `MutationVerbsTests.setUp` to `.aw/records/plans/pending/` with `set="demo"`, `order=1`, and `slug="original"`. | Keep class-level `_FIXTURES` with short IDs or `.agents/plans/pending/` with `set="demo (demo)"` (rejected: `artifact_meta.validate_id6` rejects non-6-char IDs and `RecordBuilder(root)` writes to `.aw/records/`). | `tests/test_attention_contract.py:490-625`, `tests/test_awcmdsurf_mutation_verbs.py:39-96`, `agent_workflows/artifact_meta.py::validate_id6`. | yes |
| D-2 | How should `ReadinessReaderTests.test_agrees_with_the_schema_authority` and `tests/test_backlog.py` release-exempt/companion fixtures avoid vacuous or failing `text_only=True` reads? | Use explicit `- Readiness: {value}` text if log-format `text_only=True` omits bullets in `ReadinessReaderTests`, materialize companion release/plan and `test_validate_item_release_exempt_findings` fixtures via `RecordBuilder(repo)` (or `backlog.validate_item_state`), and assert `test_release_exempt_setter_roundtrip_and_parity` history via `artifact_meta.history`. | Leave `text_only=True` in place on those fixtures (rejected: produces vacuous `None == None` readiness comparisons and missing log fields under `89mtbl` F-02). | `tests/test_attention_priority_blocker.py:261-270`, `tests/test_backlog.py:862,1273,1696-1984`, `89mtbl` F-02, `fljn9b` E-02. | yes |
