# Review findings: ipd psm9ac

- Subject-Id: psm9ac
- Subject-Type: ipd
- Reviewed-At: 2026-11-27
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Step T
1. No - the plan converts 18 test modules inside the prepared cutover code patch (`.aw/system/cutover/metastore-code.cutover.patch`) and does not change a spec or public contract.
2. Yes - it regenerates `.aw/system/cutover/metastore-code.cutover.patch`, which patches commit/hook gates (`executed_transition_gate`, `meta_log_append_gate`, `ipd_dependency_statement_gate`) and `runner_shared.py`.
3. Yes - it converts 18 test modules across three grouped execution items (`E-02` to `E-04`) spanning backlog close, release gates, check_engine, check_meta, search, companion roots, cutover log gates/readers, overrides, index aliases/rebuild, graduation coverage, in-lane retirement, and dependency statement gates.
4. Yes - `- Scope-Paths:` lists the plan file and `.aw/system/cutover/metastore-code.cutover.patch`.
5. Yes - a mistake regenerating the cumulative code patch or retiring still-valid test coverage could silently break cutover validation or lose regression coverage across 18 test modules.
- Selected tier: `standard`

AW-TIER: standard

### Step R1: References, Scope, and Dependencies
- Checked: `.aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md`, `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md`, `.aw/records/plans/pending/20261125-metastore-314-fljn9b-make-backlog-validation-and-readers-log-aware-in-the-cutover.ipd.md`, `.aw/system/cutover/metastore-code.cutover.patch`, all 18 batch B test modules (`tests/test_backlog_handoff_close.py` through `tests/test_ipd_dependency_statement_gate.py`), `agent_workflows/specs.py`, `agent_workflows/releases.py`, `agent_workflows/backlog.py`, `agent_workflows/check_engine.py`, `agent_workflows/cli.py`, `agent_workflows/meta_cli.py`, `agent_workflows/runner_shared.py`, and `agent_workflows/hooks/ipd_dependency_statement_gate.py`.
- Found six unpatched production cutover log-awareness gaps in `.aw/system/cutover/metastore-code.cutover.patch` (`PR-001`), verified by direct probes and static inspection, blocking at least 7 batch B test modules.
- Found gitignored attempt-1 lane provenance cited as live evidence (`Concern`, `F-04`), stale Step 0 chain omitting `fljn9b`, and skipped numbering in `## Proposed changes` (`PR-004`).

### Step R2: Executability and Verification Rigor
- Checked: All 18 batch B test modules against post-cutover `artifact_meta`, `specs`, `releases`, `backlog`, `check_engine`, `cli`, `meta_cli`, and `ipd_dependency_statement_gate` behavior.
- Direct probes confirmed: (a) `specs.validate_spec` emits `attention.history-missing` on a conformant log-format spec (`specs.run_check` and `check_engine.py:1624` / `runner_shared.py:9180,25362` still call `validate_spec`); (b) `releases.validate_release` emits `release.version-missing` on a conformant log-format release (and `releases.check_from_backlog:792` calls `_meta.read_text(text).fields.get("from_backlog")`); (c) `check_engine.parse_cited_spec_ids` returns `[]` on a log-format plan with `## Concern` (and `check_plan_spec_link_missing:10014` reads `_declared_bullet_fields(text).get("scope_paths")`); (d) `.aw/system/cutover/metastore-code.cutover.patch:2602` removed the only `writing_standard_pointer("backlog item")` emitter for `backlog.run_new`; (e) `cli._run_search:17821-17855` non-`--full` search scans only YAML fence + H1 and never searches log-stored `title`/`summary`/`short_description`; (f) `ipd_dependency_statement_gate._staged_ipd_overlay:68` ignores staged `meta/<id6>.jsonl` files (`PR-001`).
- Identified Phase-B / removed-behavior test traps in `test_check_meta.py`, `test_cutover_log_gates.py`, `test_cutover_log_readers.py`, `test_event_overrides.py`, and `test_companion_record_owner_root.py` (`PR-002`).
- Identified per-module removed-API, `text_only=True`, and post-cutover assertion traps across all 18 modules (`PR-003`).
- Verified `V-02`..`V-04` lacked exact `rg` patterns (`PR-004`), and `E-01`/`E-05`/`V-01`/`V-05`/`Deferred`/`Approval and execution gate` omitted exact patch/plan paths, `git status --short`, `cxxmyv`, and conditional runner-lane vs. hand-run `aw ipd finalize` ownership (`PR-005`).

### Step R3: Security, Isolation, and Safety
- Checked: Scratch worktree isolation (`.aw/state/psm9ac/scratch`), live-tree safety, `- Scope-Paths:` fence, `aw commit psm9ac` path-scoped commit contract, never-push rule, and no assertion-weakening rule.
- Added explicit `git status --short` verification in `E-05`/`V-05` to confirm no live code edits escape `- Scope-Paths:`.

### Step R4: Engineering Quality and Contract Conformance
- Checked: Technical writing standard (`.aw/system/workflows/technical-writing/technical-writing.md`), `IPD-Z603` sizing, `E-*`/`V-*` bijection, Mermaid diagram consistency, and `check.review-finding-unescalated` / `MD-9` open-question rules.
- Confirmed `PR-001` is properly escalated into `OQ-01` carrying `- Blocking: yes`, `- Status: open`, `- Owner: maintainer`, `- Finding: PR-001`, `- Carrier: ldfefd`, and a strength-labeled recommendation (`strength: strong`).

### Step S5: Open Questions and Decisions
- Checked: Collected all 5 findings; resolved `PR-002` through `PR-005` from repository evidence (all `Overall:Low`, `Reversible: yes`, recorded in `### Decisions` `D-1..D-4`).
- Escalated `PR-001` (`Overall:Medium-High`) as blocking human-owned question `OQ-01` in `psm9ac` and as `batch-b-production-log-aware-gaps` (`gates_verdict: true`) in `.aw/state/lane-submissions/run-20261126T020242Z-3080634/05-psm9ac/attempt-1/outcomes/05-psm9ac.json` because adding six production-code fixes across `specs.py`, `releases.py`, `backlog.py`, `check_engine.py`, `cli.py`, `runner_shared.py`, and `hooks/ipd_dependency_statement_gate.py` changes plan scope and sequencing across batch B and later batches.

### Pass 2: Verification of Edits
- Re-read the revised plan `.aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md` from top to bottom.
- Verified `PR-002` through `PR-005` are fully applied, `PR-001` is escalated to `OQ-01` with `- Blocking: yes` and `- Finding: PR-001`, `- Review-Depth: standard` and `- Readiness: no-go` are written, `## Workflow history` leads with `REVIEWED - OPEN QUESTIONS`, `E-01..E-05` match `V-01..V-05` 1:1, and the Mermaid diagram matches the ordered steps.

### Findings
| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | repo-wide | Production cutover readiness (`specs.py`, `releases.py`, `backlog.py`, `check_engine.py`, `cli.py`, `ipd_dependency_statement_gate.py`) | `.aw/system/cutover/metastore-code.cutover.patch:2602`; `agent_workflows/specs.py:263,662`; `agent_workflows/releases.py:68,415,569,792`; `agent_workflows/check_engine.py:1624,1901,9926,10014`; `agent_workflows/cli.py:17821`; `agent_workflows/runner_shared.py:9180,25362`; `agent_workflows/hooks/ipd_dependency_statement_gate.py:68` | Six unpatched production cutover gaps in `.aw/system/cutover/metastore-code.cutover.patch` directly block at least 7 batch B test modules (`test_blocks_release_reader_bounding`, `test_check_engine`, `test_check_engine_from_spec_missing`, `test_cli_search`, `test_from_backlog_cardinality`, `test_generators_writing_standard_pointer`, `test_ipd_dependency_statement_gate`): `specs.validate_spec`/`run_check` fails on log-format specs (`attention.history-missing`); `releases.validate_release`/`check_from_backlog`/`check_graduated_to` reads inline text only (`release.version-missing`, empty `check_from_backlog`); `backlog.run_new` lost `writing_standard_pointer("backlog item")`; `check_engine.parse_cited_spec_ids`/`check_plan_spec_link_missing` reads only legacy bullets; `cli._run_search` non-`--full` mode ignores log metadata; `ipd_dependency_statement_gate` ignores staged `meta/<id6>.jsonl`. | C:Medium-High; U:Medium; S:Low; F:High; Overall:Medium-High | OPEN | Escalated to maintainer as `OQ-01` (`- Blocking: yes`, `- Finding: PR-001`) and parked in outcome JSON (`gates_verdict: true`) to decide between a dedicated production-fix child plan ahead of `psm9ac` (plus folding the `backlog.run_new` pointer fix into `fljn9b`; Recommended, `strong`), splitting by subsystem, or expanding `psm9ac`. |
| PR-002 | BLOCKER | plan-local | E-02 & E-03 (Phase-B / removed-behavior test disposal) | `tests/test_check_meta.py:213,518`; `tests/test_cutover_log_gates.py:290,407,606`; `tests/test_cutover_log_readers.py:234,249,328`; `tests/test_event_overrides.py:246,272,299`; `tests/test_companion_record_owner_root.py:618-737` | Batch B contains multiple tests whose subject is explicitly removed Phase-B (`metadata_schema < 2` / legacy bullet format) or retired `history.jsonl` sidecar behavior, which cannot be converted to log format without contradicting their test names and spec `4sd62s` Sections 4.2, 4.3, 4.4, 4.6, 5.2, and C6. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit per-module rule-4 retirement and spec `4sd62s` citation guidance in `E-02` item 6 and `E-03` items 2 to 5 (`D-1`). |
| PR-003 | HIGH | plan-local | E-02, E-03, E-04 (per-module conversion traps) | `tests/test_backlog_handoff_close.py:980,1119`; `tests/test_blocks_release_reader_bounding.py:37,270`; `tests/test_check_engine_from_spec_missing.py:55,691`; `tests/test_from_backlog_cardinality.py:37,163,237`; `tests/test_generators_writing_standard_pointer.py:16-30`; `tests/test_index_aliases.py:375-378`; `tests/test_index_rebuild.py:134`; `tests/test_ipd_dependency_statement_gate.py:57,332` | Bare module lists in `E-02`..`E-04` hid concrete removed-API calls (`LegacyRender`/`LegacyTarget`/`render_legacy_text`), removed `## Workflow history` assertions (`_assert_pointer_before_history`), inline `.md` metadata checks (`test_index_aliases.py`), `"events:0"` assertion (`test_index_rebuild.py`), and missing `meta/<id6>.jsonl` staging (`test_ipd_dependency_statement_gate.py`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit per-module conversion rules across all 18 modules in `E-02`, `E-03`, and `E-04` (`D-2`). |
| PR-004 | HIGH | plan-local | Provenance, chain list, and `rg` verification (`Concern`, `Step 0`, `F-04`, `Proposed changes`, `V-02`..`V-04`) | `.aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md:5,69,82,88,131,135,139` | `Concern` and `F-04` cited gitignored attempt-1 lane evidence absent in fresh lanes; Step 0 omitted `fljn9b` from the chain; `## Proposed changes` skipped item 3 (`1, 2, 4`); `V-02`..`V-04` omitted the exact removed-symbol `rg` pattern and exit-1 expectation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Attributed attempt-1 counts as historical `x1mmdp` provenance (anchoring execution to `89mtbl` F-04), added `fljn9b` to Step 0, fixed `Proposed changes` numbering, and specified exact `rg -n` commands and exit-1 expectations in `V-02`..`V-04` (`D-3`). |
| PR-005 | MEDIUM | plan-local | Execution gate & hygiene (`E-01`, `E-05`, `V-01`, `V-05`, `Deferred`, `Approval and execution gate`) | `.aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md:38,62,98-103,127,143,152` | `E-01`/`E-05`/`V-01` omitted exact patch and plan paths; `E-05`/`V-05` omitted `git status --short` clean-tree verification; `## Deferred / out of scope` omitted `cxxmyv`; `## Approval and execution gate` unconditionally instructed `aw ipd finalize` instead of distinguishing managed runner lanes from hand-run sessions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-01`, `E-05`, `V-01`, `V-05`, `## Deferred / out of scope`, and `## Approval and execution gate` (`D-4`). |

### Proofreading
#### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Concern` & `F-04` | Cited gitignored `.aw/state/lane-submissions/.../failing-modules.txt` as live evidence | Attributed attempt-1 counts as historical `x1mmdp` provenance; anchored execution to `89mtbl` F-04 | Accuracy & self-contained provenance |
| `Proposed changes` | Numbered `1.`, `2.`, `4.` | Numbered `1.`, `2.`, `3.` | List hygiene |
| `E-01`, `E-05`, `V-01`..`V-05` | Generic `"the docs patch"` / `"<this plan>"` / `"rg for the removed symbols"` | Named exact repo-relative patch/plan paths and exact `rg -n '...' <modules>` commands with exit 1 | Precision & verifiable evidence |

#### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| PR-001 | `## Open questions` (`OQ-01`) | Sequencing of six unpatched production cutover log-awareness gaps blocking batch B (`psm9ac`) | Maintainer decision on splitting out a prerequisite production-fix child plan vs. expanding `psm9ac` | Fold the `backlog.run_new` pointer fix into `fljn9b` and split out one dedicated production-fix child plan ahead of `psm9ac` for the five remaining non-backlog gaps | strong |

### Decisions
| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should Phase-B (`schema=None` / `not-applicable (legacy format)`) and retired `history.jsonl` sidecar tests in `test_check_meta.py`, `test_cutover_log_gates.py`, `test_cutover_log_readers.py`, `test_event_overrides.py`, and `test_companion_record_owner_root.py` be handled? | Retire removed Phase-B and sidecar-only tests under conversion rule 4 citing spec `4sd62s` Sections 4.2, 4.3, 4.4, 4.6, 5.2, and C6 in F-02, while keeping all post-cutover `schema=2` log-format tests active. | Convert Phase-B legacy tests into log-format tests under misleading names (rejected: violates conversion rule 4 and falsifies test names). | `tests/test_check_meta.py:213,518`, `tests/test_cutover_log_gates.py:290,407,606`, `tests/test_cutover_log_readers.py:234,249,328`, `tests/test_event_overrides.py:246,272,299`, `tests/test_companion_record_owner_root.py:618-737`. | yes |
| D-2 | How should `E-02`..`E-04` address module-specific traps (`_assert_pointer_before_history`, `"events:0"`, `.md` text metadata checks, and companion `meta/<id6>.jsonl` staging)? | Specify exact per-module conversion rules for all 18 batch B modules, including updating `_assert_pointer_before_history` to drop the removed `## Workflow history` requirement and staging `meta/<id6>.jsonl` in `test_ipd_dependency_statement_gate.py`. | Leave `E-02`..`E-04` as bare filename lists (rejected: hides non-mechanical assertion and fixture traps across 18 files). | Static audit of all 18 batch B test modules against `.aw/system/cutover/metastore-code.cutover.patch`. | yes |
| D-3 | How should `Concern`, `Step 0`, `F-04`, `Proposed changes`, and `V-02`..`V-04` handle gitignored census provenance, chain updates, and `rg` patterns? | Attribute attempt-1 counts as historical `x1mmdp` provenance (starting from `89mtbl` F-04), include `fljn9b` in Step 0, fix `Proposed changes` numbering, and write exact `rg -n` commands in `V-02`..`V-04`. | Keep direct citations to gitignored lane files and generic `rg` instructions (rejected: file absent in fresh lanes; generic `rg` misses removed symbols). | `.aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md`, `cugg3w` Round 1 D-4. | yes |
| D-4 | How should `E-01`, `E-05`, `V-01`, `V-05`, `## Deferred / out of scope`, and `## Approval and execution gate` align with the runner-lane execution contract? | Name exact patch/plan paths, require `git status --short` verification in `E-05`/`V-05`, list `cxxmyv` in `## Deferred / out of scope`, and distinguish managed runner lanes from hand-run sessions for `aw ipd finalize`. | Keep unconditional `aw ipd finalize` wording and generic placeholders (rejected: violates `s7-finalize.md` runner-lane ownership rule). | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-36`, `cugg3w` Round 1 D-5. | yes |

## Round 2

### Step T
1. No - `psm9ac` converts 18 test modules inside `.aw/system/cutover/metastore-code.cutover.patch`.
2. Yes - it regenerates `.aw/system/cutover/metastore-code.cutover.patch`.
3. Yes - it covers 18 test modules across `E-02`..`E-04`.
4. Yes - `- Scope-Paths:` lists the plan and `.aw/system/cutover/metastore-code.cutover.patch`.
5. Yes - regenerating the cumulative cutover code patch affects downstream batches.
- Selected tier: `standard`

AW-TIER: standard

### Step R1: References, Scope, and Dependencies
- Checked: `.aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md`, `.aw/records/plans/pending/20261125-metastore-314-fljn9b-make-backlog-validation-and-readers-log-aware-in-the-cutover.ipd.md`, `.aw/records/plans/pending/20261125-metastore-315-szykgd-make-specs-releases-spec-link-search-and-dep-gate-log-aware.ipd.md`, `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md`, and `.aw/records/plans/pending/20261109-metastore-257-x1mmdp-add-the-log-format-test-builder-switch-to-the-cutover-code-p.ipd.md`.
- Verified the `backlog.run_new` writing-standard pointer fix (`core.writing_standard_pointer("backlog item")`) was folded into Order 314 `fljn9b` (still `to-review`), and Order 315 `szykgd` chains directly after `cugg3w` (`- Item-Dependencies: executed:cugg3w`) and ahead of `psm9ac` (`- Item-Dependencies: executed:szykgd`).
- Verified `szykgd` is wired into orchestrator `63ib9r` (`Highest E allocated: 227`, `E-227`/`V-227`, `## Child IPDs` Order 315, `E-221`/`E-179`/`E-13` dependencies) and `x1mmdp` (`- Item-Dependencies:` and `## Deferred / out of scope`).
- Swept every stale open-`OQ-01`/`PR-001` reference across `psm9ac`.

### Step R2: Executability and Verification Rigor
- Checked: `E-01`..`E-05` and `V-01`..`V-05` in `psm9ac`, `szykgd`, and updated `fljn9b`.
- Verified `psm9ac` requires zero production edits outside the scratch worktree because `fljn9b` and `szykgd` land all six production cutover fixes before `psm9ac` executes.

### Step R3: Security, Isolation, and Safety
- Checked: Scratch worktree isolation, `- Scope-Paths:` fences, `aw commit` path-scoped commit contracts, and never-push clauses in `psm9ac`, `szykgd`, and `fljn9b`.

### Step R4: Engineering Quality and Contract Conformance
- Checked: Technical writing standard (`.aw/system/workflows/technical-writing/technical-writing.md`), `IPD-Z603` sizing, `E-*`/`V-*` bijection, Mermaid diagrams, and `check.review-finding-unescalated` / `IPD-Q501` gates.
- Verified `PR-001` is cleared (`FIXED`), `OQ-01` carries `- Status: resolved` and `- Owner: maintainer` citing the maintainer's 2026-11-26 answer, `- Readiness: go-pending-approval` is written in `psm9ac`, and `szykgd` is authored review-ready (`Status: to-review`) with zero `TODO` placeholders.

### Step S5: Open Questions and Decisions
- Checked: `OQ-01` (`PR-001`) resolved by the maintainer's answer to `run-20261126T020242Z-3080634` question `05-psm9ac-a1-batch-b-production-log-aware-gaps`; recorded chaining decision `D-1` below (`Reversible: yes`). Wrote empty `questions: []` to `.aw/state/lane-submissions/run-20261126T020242Z-3080634/05-psm9ac/attempt-2/outcomes/05-psm9ac.json`.

### Pass 2: Verification of Edits
- Re-read `psm9ac`, `szykgd`, and updated `fljn9b` in full; verified `aw ipd lint --phase review-finalize` on `psm9ac`, `aw ipd lint --phase author` on `szykgd`, `fljn9b`, `63ib9r`, and `x1mmdp`, and `check_review_lane_artifacts` on all modified records.

### Findings
| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | repo-wide | Production cutover readiness (`specs.py`, `releases.py`, `backlog.py`, `check_engine.py`, `cli.py`, `ipd_dependency_statement_gate.py`) | `.aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md` (`OQ-01`, `F-05`); `.aw/records/plans/pending/20261125-metastore-314-fljn9b-make-backlog-validation-and-readers-log-aware-in-the-cutover.ipd.md`; `.aw/records/plans/pending/20261125-metastore-315-szykgd-make-specs-releases-spec-link-search-and-dep-gate-log-aware.ipd.md` | Six unpatched production cutover log-awareness gaps blocking at least 7 batch B test modules and later batches. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Maintainer answered `05-psm9ac-a1-batch-b-production-log-aware-gaps` (`OQ-01`, 2026-11-26) with "Fix backlog pointer in fljn9b and split 1 production-fix plan ahead of psm9ac (Recommended)". Folded the `backlog.run_new` pointer fix into Order 314 `fljn9b`, authored Order 315 child plan `szykgd` chained after `cugg3w`, wired `szykgd` into `63ib9r` and `x1mmdp`, updated `psm9ac`'s `- Item-Dependencies:` to `executed:szykgd`, marked `OQ-01` resolved, and swept stale references across `psm9ac`. |

### Proofreading
#### Changes
| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `psm9ac` (`Concern`, `Scope`, `E-02`..`E-04`, `Step 0`, `F-05`, `Proposed changes`, `Scope check`, `Approval and execution gate`) | Described `OQ-01`/`PR-001` as open and gating batch B modules | Updated all references to resolved `OQ-01`, `fljn9b`, and prerequisite Order 315 (`szykgd`) in `- Item-Dependencies:` | Consistency & stale-wording sweep |
| `psm9ac` (`## Deferred / out of scope`) | Did not list `fljn9b` or `szykgd` | Added `fljn9b` and `szykgd` carriers for the six production log-awareness fixes | Explicit scope boundary |

#### Issues
| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | (none) | No unresolved proofreading issues remain. | None | None | very strong |

### Decisions
| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where in the serial cutover code-patch chain should Order 315 (`szykgd`) sit? | Chain `szykgd` immediately after `cugg3w` (`- Item-Dependencies: executed:cugg3w`) and set `psm9ac` to `- Item-Dependencies: executed:szykgd` (wiring `szykgd` into `63ib9r` and `x1mmdp`). | Chain `szykgd` ahead of `cugg3w` right after `fljn9b` (rejected: would require editing already-reviewed `cugg3w`, which does not need any of `szykgd`'s five fixes). | Maintainer answer to `05-psm9ac-a1-batch-b-production-log-aware-gaps` ("Fix backlog pointer in fljn9b and split 1 production-fix plan ahead of psm9ac (Recommended)"); `.aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md`; `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md`. | yes |

## Round 3

This re-review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261126T161303Z-1366371`) after `psm9ac` was demoted `reviewed -> to-review` for `[stale-review]`. The target plan `.aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings). The re-review cross-checked all 18 batch B test modules against the six production log-awareness plans authored after `psm9ac` Round 2 (`otin36` Order 316, `p109wy` Order 317, `q6fiws` Order 318, `j1f454` Order 319, `lec341` Order 320, `3e0vfy` Order 321) and later test batches (`e0g2gt` batch D, `qi0kl6` batch E). It found one `BLOCKER` cross-plan sequencing inversion (`PR-006`, `Overall:Medium-High`, escalated to the maintainer as blocking `OQ-02` and parked in outcome JSON with `gates_verdict: true`), one `MEDIUM` finding (`PR-007`), and one `LOW` finding (`PR-008`), with `PR-007` and `PR-008` fixed in place. No production code or test code was modified.

### Step T

1. No direct public-interface or spec change (converts 18 test modules inside `.aw/system/cutover/metastore-code.cutover.patch`).
2. Yes; regenerates `.aw/system/cutover/metastore-code.cutover.patch`, which carries hook/gate and runner changes.
3. Yes; converts 18 test modules across `E-02`..`E-04`, including end-to-end runner, graduation, adoption, and check-meta suites.
4. Yes; `- Scope-Paths:` lists the plan file and `.aw/system/cutover/metastore-code.cutover.patch`.
5. Yes; executing `psm9ac` ahead of the production fixes (`otin36`..`3e0vfy`) that 5 of its 18 modules exercise guarantees execution failure and stranded work.

AW-TIER: standard

### Step R1

- Checked: all 18 batch B test modules, `szykgd` (Order 315), `otin36` (Order 316), `p109wy` (Order 317), `q6fiws` (Order 318), `j1f454` (Order 319), `lec341` (Order 320), `3e0vfy` (Order 321), `tests/test_oc_runipd.py::_init_repo_with_conforming_plan` (batch D `e0g2gt`), and `tests/test_runner_shared.py::_repo_with_pending_plan` (batch E `qi0kl6`).
- Found (`PR-006`): Because `otin36`..`3e0vfy` were split during later batch C..F reviews and chained AFTER `psm9ac` (Order 309), 5 of `psm9ac`'s 18 test modules cannot pass when `psm9ac` runs at its current position:
  1. `tests/test_check_meta.py` and `tests/test_index_rebuild.py` index spec `4sd62s` Section 4.1a `.review.md` YAML mirrors alongside `op: "review"` events, which depend on `p109wy` (Order 317) to stop `artifact_meta._load_sources` from clobbering log-owned `reviews` rows and failing with `REV-M101`.
  2. `tests/test_index_aliases.py::test_producers_write_no_index_files_and_find_sees_each_change` runs `aw ipd begin`/`finalize` (needs `otin36` Order 316), `aw research mv` + `aw find` (needs `lec341` Order 320), and `aw adopt --apply` (needs `lec341` Order 320 + `3e0vfy` Order 321).
  3. `tests/test_gradcover_end_to_end.py` (run by `E-04` `-m ''`) drives `coverage_record.is_current`/`write` (needs `q6fiws` Order 318), `aw ipd set reviewed` on an orchestrator and `aw ipd set approved` (needs `3e0vfy` Order 321), and `ipd_lifecycle.retire_orchestrator` (needs `otin36` Order 316).
  4. `tests/test_inlane_retirement_lands.py` relies on `check_status_untooled_range` (needs `otin36` Order 316) and directly imports unconverted fixture builders from `tests/test_oc_runipd.py` (`e0g2gt`) and `tests/test_runner_shared.py` (`qi0kl6`).
- Verified the other 13 batch B modules do not depend on `otin36`..`3e0vfy` (notably `tests/test_companion_record_owner_root.py` line 523 only asserts the hint string `--to-id6`, and `tests/test_backlog_handoff_close.py` only uses `.review.md` as a `close_evidence` path string).

### Step R2

- Checked: E/V bijection (`5/5`), `- Scope-Paths:` (2 tracked paths), `- Item-Dependencies: executed:szykgd`, `OQ-01` (resolved) and newly escalated `OQ-02` (`Blocking: yes`, `Status: open`, `Owner: maintainer`, `Finding: PR-006`, `Carrier: ldfefd`), `V-*` evidence, re-derivation convention, `rg` patterns, and `## Approval and execution gate`.
- Found: `PR-006` breaks executability of 5 modules in `E-02` and `E-04` until resolved; `V-05` hardcoded `with all 3 tests PASSED` and `V-02`..`V-04` `rg` patterns omitted `append_legacy|restore_legacy_snapshot|LEGACY_LOADER_VERSION|meta\.load_legacy_artifact|meta\.derive_id6` (`PR-007`, fixed in place); Step 0 chain and Mermaid `E-01` branch were updated (`PR-008`, fixed in place).

### Step R3

- Checked (full form, `standard` tier):
  - Anti-regression / gate safety: surfacing `PR-006` prevents an executor from weakening assertions on `test_check_meta.py`, `test_index_rebuild.py`, `test_index_aliases.py`, `test_gradcover_end_to_end.py`, or `test_inlane_retirement_lands.py` to work around missing production fixes (`otin36`..`3e0vfy`).
  - Workspace containment: edits occur strictly inside gitignored `.aw/state/psm9ac/scratch`; no live code or secrets touched.

### Step R4

- Checked: correctness, anti-regression, testing/verification, KISS, right-sizing, and `## Spec / documentation sync`.
- Verified `PR-006` crosses multiple sibling plans outside `psm9ac`'s `- Scope-Paths:` (`Overall:Medium-High`, `Decision: OPEN`, escalated as `OQ-02`).

### Step S5

- Checked: `OQ-01` remains resolved (2026-11-26). Escalated `PR-006` into `OQ-02` (`- Blocking: yes`, `- Status: open`, `- Owner: maintainer`, `- Finding: PR-006`, `- Carrier: ldfefd`, recommendation strength `strong`) and parked `batch-b-downstream-prod-order` (`gates_verdict: true`) in `.aw/state/lane-submissions/run-20261126T161303Z-1366371/03-psm9ac/attempt-1/outcomes/03-psm9ac.json`. Fixed `PR-007` and `PR-008` in place (`Overall:Low`). Set `- Readiness: no-go` and verdict `REVIEWED - OPEN QUESTIONS`.

### Pass 2

- Re-read `psm9ac` in full: verified `F-06`, `OQ-02` (`Blocking: yes`, `Finding: PR-006`, `Owner: maintainer`), `- Status: reviewed`, `- Review-Depth: standard`, `- Readiness: no-go`, `## Workflow history` leading with `REVIEWED - OPEN QUESTIONS`, `V-02`..`V-05` fixes, updated Mermaid diagram, and `## Approval and execution gate` referencing `OQ-02`.
- Verified `aw ipd lint --phase review-finalize --agent` reports only `IPD-Q501` for intentionally open blocking `OQ-02` (zero other errors or warnings).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-006 | BLOCKER | IN-SCOPE | R1 / R2 / R4 / Cross-plan sequencing inversion against `otin36`..`3e0vfy` and `e0g2gt`/`qi0kl6` | `tests/test_check_meta.py:189`, `tests/test_index_rebuild.py:84`, `tests/test_index_aliases.py:293-406`, `tests/test_gradcover_end_to_end.py:544-800`, `tests/test_inlane_retirement_lands.py:23-26,207-248`; `otin36` (Order 316), `p109wy` (Order 317), `q6fiws` (Order 318), `lec341` (Order 320), `3e0vfy` (Order 321), `tests/test_oc_runipd.py:2992`, `tests/test_runner_shared.py:4468` | Six production log-awareness plans (`otin36`..`3e0vfy`) split during later batch C..F reviews sit AFTER `psm9ac` (Order 309) in the serial code-patch chain, yet 5 of `psm9ac`'s 18 test modules depend on them (`test_check_meta` and `test_index_rebuild` on `p109wy`; `test_index_aliases` on `otin36`, `lec341`, `3e0vfy`; `test_gradcover_end_to_end` on `otin36`, `q6fiws`, `3e0vfy`; `test_inlane_retirement_lands` on `otin36` plus unconverted fixture builders imported from `test_oc_runipd.py` in `e0g2gt` and `test_runner_shared.py` in `qi0kl6`). | C:Medium-High; U:Medium; S:Low; F:High; Overall:Medium-High | OPEN | Escalated to maintainer as blocking `OQ-02` (`- Blocking: yes`, `- Finding: PR-006`) and parked in outcome JSON (`gates_verdict: true`) to decide between re-chaining all 6 production-fix plans (`otin36`..`3e0vfy`) ahead of test batches `psm9ac`..`x3mig6` and localizing the two imported helpers in `test_inlane_retirement_lands.py` (Recommended, `strong`), moving the 5 modules out of `psm9ac` to a final batch after `3e0vfy`/`qi0kl6`, or deferring their failures to `x1mmdp`. Recommendation strength: strong. |
| PR-007 | MEDIUM | IN-SCOPE | R2 / Re-derivation convention (`V-05` test count) and `V-02`..`V-04` `rg` pattern | plan `V-05` (`with all 3 tests PASSED`), `V-02`..`V-04` (`rg` pattern); `.aw/system/workflows/plan-review/steps/r2-executability.md` | `V-05` hardcoded a collected test count (`all 3 tests PASSED`) contrary to the re-derivation convention, and `V-02`..`V-04` `rg` patterns omitted `append_legacy`, `restore_legacy_snapshot`, `LEGACY_LOADER_VERSION`, `meta\.load_legacy_artifact`, and `meta\.derive_id6`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced `with all 3 tests PASSED` in `V-05` with pinned guard-test behaviors and expanded `V-02`..`V-04` `rg` patterns. Recommendation strength: very strong. |
| PR-008 | LOW | IN-SCOPE | Check P / Technical writing requirement 12 (diagram) and chain/gate sync | plan Step 0 chain, `## Proposed changes` Mermaid flowchart, `## Approval and execution gate`; `.aw/system/workflows/technical-writing/technical-writing.md` requirement 12(b)/(d) | Step 0 omitted the post-split production-fix children (`otin36`..`3e0vfy`), the Mermaid diagram omitted the `E-01` patch-rejection stop branch, and `## Approval and execution gate` needed to reflect open blocking `OQ-02`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated Step 0's serial chain, added the `Patches apply cleanly?` stop branch to the Mermaid diagram, and updated `## Approval and execution gate` to gate execution on `OQ-02`. Recommendation strength: strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `F-06`, `## Open questions` (`OQ-02`), `## Approval and execution gate` | Assumed `fljn9b` and `szykgd` unblocked all 18 batch B modules | Documented the 5 modules blocked by later `otin36`..`3e0vfy` and `e0g2gt`/`qi0kl6` helpers (`F-06`) and escalated blocking `OQ-02` | PR-006 |
| `V-02`..`V-05` | Narrower `rg` pattern; hardcoded `with all 3 tests PASSED` in `V-05` | Expanded removed-symbol `rg` pattern across `V-02`..`V-04` and behavioral guard-test check in `V-05` | PR-007 |
| Step 0, `## Proposed changes` Mermaid flowchart | Short chain list; linear Mermaid diagram | Complete current serial chain (`hdwqex`..`0zylig`) and E-01 stop branch in Mermaid diagram | PR-008 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| PR-006 | `## Open questions` (`OQ-02`) | Sequencing of 5 batch B test modules against later production-fix plans (`otin36`..`3e0vfy`) and imported test-batch helpers (`e0g2gt`/`qi0kl6`) | Maintainer decision on re-chaining all remaining production-fix plans ahead of test batches B through F vs. moving the 5 modules out of `psm9ac` vs. deferring failures to `x1mmdp` | Re-chain `otin36`..`3e0vfy` ahead of test batches `psm9ac`..`x3mig6` and localize the two imported fixture helpers in `tests/test_inlane_retirement_lands.py` | strong |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| (none) | All non-escalated fixes (`PR-007`, `PR-008`) are mechanical rule compliance; `PR-006` is escalated to the maintainer as `OQ-02` rather than decided unilaterally. | Escalated `PR-006` to maintainer (`OQ-02`, `gates_verdict: true`). | Re-chain sibling plans unilaterally inside `psm9ac` review (rejected: changes `- Item-Dependencies:` across 7+ sibling plans outside `psm9ac`'s scope). | `steps/_findings.md`, `steps/s5-questions.md`, `tests/test_check_meta.py`, `tests/test_index_rebuild.py`, `tests/test_index_aliases.py`, `tests/test_gradcover_end_to_end.py`, `tests/test_inlane_retirement_lands.py`. | yes |


## Round 4

### Step T

1. No direct public-interface or spec change (converts 18 batch B test modules inside `.aw/system/cutover/metastore-code.cutover.patch`).
2. Yes; regenerates `.aw/system/cutover/metastore-code.cutover.patch`.
3. Yes; converts 18 test modules across `E-02`..`E-04` and re-chains sibling plans per maintainer Option 1 answer to `OQ-02`.
4. Yes; `- Scope-Paths:` lists the plan file and `.aw/system/cutover/metastore-code.cutover.patch`.
5. Yes; resolving `PR-006` clears the cross-plan sequencing inversion across batches B through F.

AW-TIER: standard

### Step R1

- Checked: `psm9ac` and all re-chained sibling plans (`szykgd`, `otin36`, `p109wy`, `q6fiws`, `j1f454`, `lec341`, `3e0vfy`, `x8id25`, `e0g2gt`, `qi0kl6`, `x3mig6`).
- Verified the serial `- Item-Dependencies:` chain now runs all six remaining production-fix plans (`otin36 -> p109wy -> q6fiws -> j1f454 -> lec341 -> 3e0vfy`) right after `szykgd` and ahead of all five remaining test batches (`psm9ac -> x8id25 -> e0g2gt -> qi0kl6 -> x3mig6 -> x1mmdp`) with zero cycles.
- Verified `psm9ac` `E-04` item 5 now localizes the two imported fixture helpers (`_conforming_plan_text`/`_init_repo_with_conforming_plan` from `tests/test_oc_runipd.py` and `_repo_with_pending_plan`/`_verified_lane`/`_write_run_state`/`_stranded_item` from `tests/test_runner_shared.py`) inside `tests/test_inlane_retirement_lands.py`.

### Step R2

- Checked: `E-01`..`E-05`, `V-01`..`V-05`, `OQ-01` (resolved), `OQ-02` (resolved), `- Item-Dependencies: executed:3e0vfy`, `- Readiness: go-pending-approval`, and `## Approval and execution gate`.
- Verified all 5 previously blocked batch B test modules (`test_check_meta.py`, `test_index_rebuild.py`, `test_index_aliases.py`, `test_gradcover_end_to_end.py`, `test_inlane_retirement_lands.py`) now run after every production-fix prerequisite (`otin36`..`3e0vfy`) has executed and have zero dependency on later unconverted test-batch modules.

### Step R3

- Checked: scratch worktree isolation, `- Scope-Paths:` fence, `aw commit psm9ac` path-scoped commit contract, and never-push clause remain intact.

### Step R4

- Checked: `PR-006` cleared (`Decision: FIXED`), `OQ-02` carries `- Status: resolved` and `- Owner: maintainer`, and `aw ipd lint --phase review-finalize` conforms with zero errors or warnings.

### Step S5

- Checked: maintainer answered `OQ-02` with Option 1 on 2026-11-26; no blocking open questions remain. Set `- Readiness: go-pending-approval` and verdict `APPROVE WITH REVISIONS APPLIED`.

### Pass 2

- Re-read `psm9ac` in full and validated all re-chained plans via `aw ipd lint`, `aw check plans`, and `aw attention`.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-006 | BLOCKER | IN-SCOPE | R1 / R2 / R4 / Cross-plan sequencing inversion against `otin36`..`3e0vfy` and `e0g2gt`/`qi0kl6` | `psm9ac` (`F-06`, `OQ-02`, `E-04` item 5); re-chained `- Item-Dependencies:` across `otin36`, `p109wy`, `j1f454`, `3e0vfy`, `psm9ac`, `x8id25`, `e0g2gt`, `qi0kl6`, `x3mig6` | Five batch B test modules depended on production-fix plans `otin36`..`3e0vfy` chained after `psm9ac` and on two imported helpers from `e0g2gt`/`qi0kl6`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Maintainer chose Option 1 (2026-11-26). Re-chained `otin36 -> p109wy -> q6fiws -> j1f454 -> lec341 -> 3e0vfy` ahead of `psm9ac -> x8id25 -> e0g2gt -> qi0kl6 -> x3mig6` via `aw ipd dependencies set`, updated `psm9ac` `E-04` item 5 to localize the two imported fixture helpers inside `tests/test_inlane_retirement_lands.py`, marked `OQ-02` resolved, set `- Readiness: go-pending-approval`, and swept stale open-`OQ-02` references across `psm9ac`. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `psm9ac` (`Scope`, `E-04` item 5, `Step 0`, `F-06`, `Proposed changes`, `Scope check`, `OQ-02`, `Approval and execution gate`) | Treated `OQ-02`/`PR-006` as open and chained `psm9ac` directly after `szykgd` | Resolved `OQ-02` (Option 1), updated chain to `executed:3e0vfy`, added helper localization in `E-04` item 5, set `- Readiness: go-pending-approval` | PR-006 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | (none) | No unresolved proofreading issues remain. | None | None | very strong |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How to apply Option 1 re-chaining across already-`approved` sibling plans without inducing `[stale-review]` on unchanged execution checklists? | Updated `- Item-Dependencies:` via `aw ipd dependencies set` across all 9 affected plans (leaving `frozen_region_digest` unchanged on already-`approved` plans) and updated `otin36` (`to-review`) and `psm9ac` prose in full. | Rewrite `- Scope:` prose on all 7 already-`approved` plans (rejected: modifies `frozen_region_digest` and invalidates human approval unnecessarily when only the dependency edge moved). | Maintainer Option 1 answer (2026-11-26); `agent_workflows/ipd_lifecycle.py::frozen_region_digest`; `agent_workflows/plan_readiness.py::review_staleness_from_texts`. | yes |



## Round 5

This re-review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261127T041632Z-1918738`) after `psm9ac` was demoted `reviewed -> to-review` via `aw agy review` following Round 4 and the follow-up reviews of prerequisites `fljn9b` (`f709b0b27`), `szykgd` (`f9aaab507`), and `otin36` (`91dbc96c2`). The only uncommitted working-tree diff at start was the runner's `reviewed -> to-review` demotion (stripping `- Readiness:`), so no separate pre-review snapshot commit was made. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings). The re-review audited all 18 batch B test modules (`tests/test_backlog_handoff_close.py` through `tests/test_ipd_dependency_statement_gate.py`), the full serial prerequisite chain (`hdwqex` -> `89mtbl` -> `nv3upa` -> `fljn9b` -> `cugg3w` -> `szykgd` -> `otin36` -> `p109wy` -> `q6fiws` -> `j1f454` -> `lec341` -> `3e0vfy` -> `psm9ac` -> `x8id25` -> `e0g2gt` -> `qi0kl6` -> `x3mig6` -> `x1mmdp` -> `0zylig`), `tests/test_metastore_cutover_code_patch.py`, `tests/repo_template.py`, and production implementations (`check_engine.py`, `meta_cli.py`, `ipd_lint.py`, `hooks/ipd_dependency_statement_gate.py`). It identified three `HIGH` plan-local test-conversion trap findings (`PR-009`..`PR-011`) and one `LOW` scope-sync finding (`PR-012`), all `Overall:Low` remediation risk and all fixed in place. No production code or test code was modified.

### Step T

1. No - the plan converts 18 test modules inside `.aw/system/cutover/metastore-code.cutover.patch` and does not change a spec or public contract.
2. Yes - it regenerates `.aw/system/cutover/metastore-code.cutover.patch`, which patches commit/hook gates (`executed_transition_gate`, `meta_log_append_gate`, `ipd_dependency_statement_gate`) and `runner_shared.py`.
3. Yes - it converts 18 test modules across `E-02`..`E-04` spanning backlog close, release gates, check_engine, check_meta, search, companion roots, cutover log gates/readers, overrides, index aliases/rebuild, graduation coverage, in-lane retirement, and dependency statement gates.
4. Yes - `- Scope-Paths:` lists the plan file and `.aw/system/cutover/metastore-code.cutover.patch`.
5. Yes - a mistake regenerating the cumulative code patch or mis-converting test fixtures/assertions could silently weaken regression coverage or fail execution across 18 test modules.

AW-TIER: standard

### Step R1

- Checked: `psm9ac`, all 18 batch B test modules (`tests/test_backlog_handoff_close.py` through `tests/test_ipd_dependency_statement_gate.py`), the entire serial dependency chain (`hdwqex`, `89mtbl`, `nv3upa`, `fljn9b`, `cugg3w`, `szykgd`, `otin36`, `p109wy`, `q6fiws`, `j1f454`, `lec341`, `3e0vfy`, `psm9ac`, `x8id25`, `e0g2gt`, `qi0kl6`, `x3mig6`, `x1mmdp`, `0zylig`, `63ib9r`, `cxxmyv`), spec `4sd62s` (`.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md`, pre-cutover date `20260925`), executed `2k5t16`, `tests/test_metastore_cutover_code_patch.py`, `tests/repo_template.py`, `tests/test_runner_shared.py::_passing_suite`, `agent_workflows/check_engine.py` (`_check_untooled_plan_transition`, `evaluate_blocking_close`, `check_release_gate_consistency`, `_meta_records_with_fields`, `check_spec_criteria_uncovered`), `agent_workflows/meta_cli.py::index_rebuild`, `agent_workflows/ipd_lint.py::run_lint`, and `agent_workflows/hooks/ipd_dependency_statement_gate.py`.
- Confirmed: `- Item-Dependencies: executed:3e0vfy` sits cleanly at the end of all production-fix plans (`hdwqex`..`3e0vfy`) with zero remaining production log-awareness inversions across all 18 batch B modules.
- Found concrete per-module conversion traps missed in `E-02`..`E-04`:
  - `tests/test_inlane_retirement_lands.py`: prepending `"RETIRED 2026-09-27: premise spent.\n\n"` before line-1 `---` corrupts the YAML mirror; `tooled=False` must hand-edit only the mirror `status:` line (not call `artifact_meta.append`) and align the `untooled_status_refusal` assertion with `otin36` E-03 item 2; `_setup_repo_and_carriers` needs `RecordBuilder(repo)` materialization; line 273 imports `_passing_suite` from unconverted `tests/test_runner_shared.py` (`PR-009`).
  - `tests/test_backlog_handoff_close.py` (`test_case_6b` bullet-strip no-op on log-backed `close_evidence`, `test_case_6c` `text_only=True` after unlink), `tests/test_blocks_release_reader_bounding.py` (`test_loose_blocks_release_cases` Case 1 needing legacy bullet input, six body-quote tests placing `- Blocks-Release:` inside `history=` instead of `body=`), `tests/test_check_engine_from_spec_missing.py` (`_create_plan` using `raw_fields` instead of `## Concern`/`## Scope` body sections, `test_cited_in_scope_paths`/`test_deduplication_across_bullets` passing `text_only=True` with no `state=`), and `tests/test_check_engine_spec_criteria.py` (`test_counterfactual_pin_matches_motivating_defect_set` calling `check_spec_criteria_uncovered` on unmigrated commit `516eb661` bullet files without running `aw migrate metadata` first; `test_plan_gaining_from_spec_edge_uncovers_criteria` regex-stripping `- From-Spec:`) (`PR-010`).
  - `tests/test_from_backlog_cardinality.py` (`test_cross_reader_parity_matrix` feeding `text_only=True` to pure-text legacy readers and leaking `meta/tstpln.jsonl` across subtest iterations; 5-char `"valid"` id and non-enum `Status: pending`), `tests/test_gradcover_end_to_end.py` (text-only `coverage_record.is_current(orch_txt_a)` missing `plan_path`/`repo`, inline `- Coverage:`/`read_text` checks), and `tests/test_index_aliases.py` (`_completed_plan("al0005")` written text-only without `meta/al0005.jsonl`) (`PR-011`).
  - `## Deferred / out of scope` omitted the six re-chained production-fix plans `otin36`..`3e0vfy` (`PR-012`).

### Step R2

- Checked: E/V bijection (`5/5`: `E-01..E-05` to `V-01..V-05`, `- Highest E allocated: 05`), `- Scope-Paths:` (2 tracked paths), `- Item-Dependencies: executed:3e0vfy`, `OQ-01` (resolved) and `OQ-02` (resolved), `V-01..V-05` concrete evidence demands (exact `rg -n` patterns, both-tier pytest commands, guard-test behavioral outcomes with no hardcoded test counts), runtime-demonstration reachability (all `V-*` items are reachable by construction), durable carriers (`fljn9b`, `szykgd`, `3e0vfy`, `x8id25`, `x1mmdp`, `cxxmyv`), and `## Approval and execution gate` execution contract (scope-fence declaration without stop-on-scope-question, hard-MUST honesty rule, `aw commit psm9ac`, never-push, conditional managed-runner vs. hand-run `aw ipd finalize`).
- Found: all checks pass after applying `PR-009`..`PR-012`.

### Step R3

- Checked (full form, `standard` tier):
  - Workspace containment and isolation: all code/test edits occur solely in gitignored `.aw/state/psm9ac/scratch`, removed before committing; `E-05`/`V-05` verify `git status --short` shows only `- Scope-Paths:` modified.
  - Anti-regression / gate integrity: surfacing `PR-009`..`PR-011` prevents an executor from accidentally weakening untooled-retirement, close-evidence, body-quote, or coverage-cache assertions when converting the 18 batch B modules.
  - Secrets/trust boundaries: no secrets, credentials, outbound calls, or privileged bypasses; path-scoped `aw commit psm9ac`, never push.

### Step R4

- Checked: correctness, architecture/reuse, anti-regression, testing/verification, KISS, right-sizing and conceptual density (`5` E-items, `3` task groups, `2` Scope-Paths, 6 contiguous modules per conversion step matching the maintainer-approved `x1mmdp` split), technical writing standard (including requirement 12 Mermaid flowchart parity and `path::Symbol` citations), and `## Spec / documentation sync`.
- Verified: all four findings (`PR-009`..`PR-012`) are `Overall:Low` remediation risk and fixed in place.

### Step S5

- Checked: `OQ-01` and `OQ-02` remain resolved (2026-11-26, maintainer). Zero new human decisions arose; all four findings (`PR-009`..`PR-012`) are settled by repository code evidence (`Reversible: yes`, recorded in `### Decisions` `D-1..D-3`). Wrote `"questions": []` to `.aw/state/lane-submissions/run-20261127T041632Z-1918738/01-psm9ac/attempt-1/outcomes/01-psm9ac.json`.

### Pass 2

- Re-read revised `.aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md` in full: verified `- Status: reviewed`, `- Review-Depth: standard`, `- Readiness: go-pending-approval`, `## Workflow history` leading with `APPROVE WITH REVISIONS APPLIED`, all `PR-009`..`PR-012` revisions in `E-02`..`E-04` and `## Deferred / out of scope`, `E-01..E-05` / `V-01..V-05` 1:1 bijection, and Mermaid diagram parity.
- Ran `aw ipd lint --phase review-finalize --agent` on `psm9ac` (exit 0, `clean`, 0 findings).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-009 | HIGH | IN-SCOPE | R1 / R2 / `E-04` item 5 (`tests/test_inlane_retirement_lands.py`) | `tests/test_inlane_retirement_lands.py::_fake_agent_retires_in_lane:89-118`, `test_hand_retirement_receives_fix_it_turn:207-232`, `test_retired_lane_reintegrates_and_is_marked_retired:273`, `_setup_repo_and_carriers:346-375`; `otin36` E-03 item 2 | `E-04` item 5 missed four concrete log-format traps in `tests/test_inlane_retirement_lands.py`: prepending `"RETIRED 2026-09-27: premise spent.\n\n"` before line-1 `---` destroys the YAML mirror; `tooled=False` must hand-edit only the YAML mirror `status:` line (not call `artifact_meta.append`) and update its `"Workflow history"` assertion to match `otin36` E-03 item 2's mirror-vs-log refusal; `_setup_repo_and_carriers` writes `text_only=True` fixtures; and line 273 still imports `_passing_suite` from unconverted batch E `tests/test_runner_shared.py`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-04` item 5 to specify post-mirror retirement-note insertion, mirror-only `tooled=False` hand-edit and updated refusal assertion, `RecordBuilder(repo)` materialization in `_setup_repo_and_carriers`, and localization of `_passing_suite` alongside the other imported helpers (`D-1`). Recommendation strength: very strong. |
| PR-010 | HIGH | IN-SCOPE | R1 / R2 / `E-02` items 1, 2, 4, 5 (first-third conversion traps) | `tests/test_backlog_handoff_close.py:888-928`; `tests/test_blocks_release_reader_bounding.py:62-74,123,195,296,380,431,503`; `tests/test_check_engine_from_spec_missing.py:107-150,170-178,206-217`; `tests/test_check_engine_spec_criteria.py:338-424,455-457`; `agent_workflows/check_engine.py::evaluate_blocking_close`, `check_spec_criteria_uncovered` | Four first-third modules in `E-02` carried unmentioned log-format traps: `test_backlog_handoff_close.py` (`test_case_6b` stripping `- Close-Evidence:` from `.backlog.md` is a no-op against `meta/item01.jsonl`, `test_case_6c` writes `text_only=True` after unlinking `item_path`); `test_blocks_release_reader_bounding.py` (`test_loose_blocks_release_cases` Case 1 needs literal legacy bullet input, and six body-quote tests put `- Blocks-Release:` in `history=` instead of `body=`); `test_check_engine_from_spec_missing.py` (`_create_plan` uses `raw_fields` instead of `## Concern`/`## Scope` body sections, and two `parse_cited_spec_ids` tests omit `state=` on `text_only=True`); and `test_check_engine_spec_criteria.py` (`test_counterfactual_pin_matches_motivating_defect_set` runs `check_spec_criteria_uncovered` on unmigrated commit `516eb661` bullet files without `aw migrate metadata`, and `test_plan_gaining_from_spec_edge_uncovers_criteria` regex-strips `- From-Spec:`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit per-module log-format conversion instructions to `E-02` items 1, 2, 4, and 5 (`D-2`). Recommendation strength: very strong. |
| PR-011 | HIGH | IN-SCOPE | R1 / R2 / `E-03` item 6 and `E-04` items 2, 3 (`from_backlog_cardinality`, `gradcover_end_to_end`, `index_aliases`) | `tests/test_from_backlog_cardinality.py:96-162,299-351,427`; `tests/test_gradcover_end_to_end.py:544-548,613-616,995-998,1292-1293,1316-1317`; `tests/test_index_aliases.py:243-260,305-307`; `q6fiws` E-02 item 1 | Three modules in `E-03` and `E-04` had unmentioned traps: `test_from_backlog_cardinality.py` passes `text_only=True` to pure-text legacy readers, leaks `meta/tstpln.jsonl` across subtest iterations when unlinking only `plan_file`, uses 5-char `"valid"` id, and sets non-enum `Status: pending`; `test_gradcover_end_to_end.py` calls text-only `coverage_record.is_current(orch_txt_a)` without `plan_path`/`repo` and asserts inline `- Coverage:` / `read_text` readiness instead of `artifact_meta.read`/`history`; and `test_index_aliases.py` writes `_completed_plan("al0005")` text-only without `meta/al0005.jsonl`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit per-module instructions to `E-03` item 6 and `E-04` items 2 and 3 (`D-3`). Recommendation strength: very strong. |
| PR-012 | LOW | IN-SCOPE | Check P / R2 / `## Deferred / out of scope` sync with `OQ-02` Option 1 | `psm9ac` `## Deferred / out of scope`, `F-06`, `OQ-02` | `## Deferred / out of scope` listed `fljn9b` and `szykgd` (from `OQ-01`) but omitted the six re-chained production log-awareness plans `otin36`..`3e0vfy` (from `OQ-02` Option 1). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the `otin36`..`3e0vfy` entry carrying `- Carrier: 3e0vfy` to `## Deferred / out of scope`. Recommendation strength: strong. |

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `E-02` items 1, 2, 4, 5 | High-level per-module conversion notes omitting `test_case_6b`/`6c`, `history=` body-quote placement, `## Concern`/`## Scope` body sections, and `516eb661` migration | Explicit log-format conversion instructions covering each verified trap | PR-010 |
| `E-03` item 6 & `E-04` items 2, 3, 5 | Omitted subtest `meta/tstpln.jsonl` cleanup, `coverage_record.is_current(plan_path=, repo=)`, `_completed_plan("al0005")` materialization, post-mirror retirement note placement, mirror-only `tooled=False` hand-edit, and `_passing_suite` localization | Added exact per-module rules for every verified trap | PR-009, PR-011 |
| `## Deferred / out of scope` | Listed `fljn9b` and `szykgd` only | Added `otin36`..`3e0vfy` (`- Carrier: 3e0vfy`) matching `OQ-02` Option 1 | PR-012 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | (none) | No unresolved proofreading issues remain. | None | None | very strong |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `tests/test_inlane_retirement_lands.py` handle the retirement note, `tooled=False` hand-edit simulation, `_setup_repo_and_carriers`, and `_passing_suite` import on the post-cutover log format? | Insert the retirement note after the YAML mirror/banner, simulate `tooled=False` by hand-editing only the YAML mirror `status:` line (matching `otin36` E-03 item 2's mirror-vs-log `check.status-untooled` refusal), materialize `_setup_repo_and_carriers` via `RecordBuilder(repo)`, and localize `_passing_suite` alongside the other imported helpers. | Prepend text before `---` or call `artifact_meta.append` for `tooled=False` (rejected: corrupts the YAML mirror or creates a tooled transition that never triggers `check.status-untooled`); keep importing `_passing_suite` from unconverted `tests/test_runner_shared.py` (rejected: unnecessary cross-batch import). | `tests/test_inlane_retirement_lands.py:89-118,207-232,273,346-375`; `otin36` E-03 item 2. | yes |
| D-2 | How should `E-02` handle the log-format fixture and legacy-input traps in `test_backlog_handoff_close.py`, `test_blocks_release_reader_bounding.py`, `test_check_engine_from_spec_missing.py`, and `test_check_engine_spec_criteria.py`? | Unset `close_evidence` via `artifact_meta.append` in `test_case_6b`; keep literal legacy bullet input in `test_loose_blocks_release_cases` Case 1 and move body-quoted `- Blocks-Release:` lines from `history=` into `body=`; emit `## Concern`/`## Scope` body sections in `_create_plan` and pass `state=`/`## Concern`/`## Scope` or legacy bullet text in `parse_cited_spec_ids` unit tests; run `aw migrate metadata` on the commit `516eb661` temp repo in `test_counterfactual_pin_matches_motivating_defect_set`. | Leave generic `RecordBuilder(repo)` wording (rejected: each of those four cases would fail or silently test the wrong thing on log-format fixtures). | `tests/test_backlog_handoff_close.py:888-928`; `tests/test_blocks_release_reader_bounding.py:62-74,123,195,296,380,431,503`; `tests/test_check_engine_from_spec_missing.py:107-150,170-178,206-217`; `tests/test_check_engine_spec_criteria.py:338-424,455-457`; `agent_workflows/check_engine.py::evaluate_blocking_close`, `check_spec_criteria_uncovered`. | yes |
| D-3 | How should `E-03` item 6 and `E-04` items 2 and 3 handle `test_from_backlog_cardinality.py`, `test_gradcover_end_to_end.py`, and `test_index_aliases.py`? | Use explicit legacy bullet strings for pure-text legacy readers in `test_cross_reader_parity_matrix` and unlink `meta/tstpln.jsonl` between subtests (with valid 6-char id6s and post-cutover IPD statuses); pass `plan_path`/`repo` to `coverage_record.is_current` and read coverage/readiness via `artifact_meta.read`/`history` in `test_gradcover_end_to_end.py`; materialize `_completed_plan("al0005")` via `RecordBuilder(repo)` in `test_index_aliases.py`. | Leave `text_only=True` or text-only `coverage_record.is_current` calls unchanged (rejected: causes guaranteed failures on log-format records). | `tests/test_from_backlog_cardinality.py:96-162,299-351,427`; `tests/test_gradcover_end_to_end.py:544-548,613-616,995-998,1292-1293,1316-1317`; `tests/test_index_aliases.py:243-260,305-307`; `q6fiws` E-02 item 1. | yes |
