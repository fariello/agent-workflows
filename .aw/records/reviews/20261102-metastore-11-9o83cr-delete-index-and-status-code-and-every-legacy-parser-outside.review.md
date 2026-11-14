# Review findings: plan 9o83cr

- Subject-Id: 9o83cr
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `6e4f9ecdf` in a non-interactive runner review-sweep lane worktree, after the same lane reviewed `ffceq0` and `t4gl15`. The lane-input copy (revision 12) is byte-identical to the tracked plan, which was committed and unmodified, so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-01, E-03, E-16, V-01, V-03, V-11, V-16 | Baselines from `aw check plans --agent` / `aw check --agent` | Baselines with `--all`, which is the only path that reaches `check_drift` | PR-001. |
| E-02, V-02 | `--check` runs "the surviving content drift rules" | Prompts' `name-metadata-mismatch` is wired into `check_engine.check_content` so it survives | PR-002. |
| Item-Dependencies, OQ-05 (new), gate | `ffceq0`, `t4gl15`, `59aiyh` | Adds `1ajqaa` and `dcerjg` | PR-003. |
| E-01, E-12, Scope-Paths, V-12 | `agent_workflows` only | `tools/gate_drop_audit.py` callers found and retargeted | PR-004. |
| E-10, V-10 | Moving `newest_history_record` without its migration caller | `m0001_convert` calls the moved function; migration tests stay green | PR-005. |
| E-11, V-11 | Delete `read_front_matter_id` | The `_read_id` re-exports rebind to `read_text`'s loose value; the cross-host test passes unchanged | PR-006. |
| E-01, E-14, V-01, V-06, V-14 | `/tmp/opencode/...` | `.aw/state/9o83cr/`; exclusions copied into F-21 | PR-007. |
| PIN RULE (new), E-08, V-08 | "equal passed counts" | Outcome lists; retargets map removed names to successors | PR-008. |
| OQ-03, gate | "the executor stops after E-11" | Finish E-11, record the rest as follow-on rows, report | PR-009. |
| Gate, E-16 | Partial execution contract | Full contract | PR-010. |
| OQ-01 to OQ-04 | No recommendation strength | Strength stated | Proofreading (MD-9). |
| E-03 | `run_find` kept for `prompts_index` | `prompts_index` has no `run_find`; keep `scan_prompts` and `check_drift` | Proofreading (R1). |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `aw index <type>` becomes an alias, two rule ids and several public module functions are deleted, and the docs change.
2. No guard module is edited. `hooks/executed_transition_gate` and `hooks/backlog_blocking_close_gate` are touched only by symbol retargets.
3. Yes. It has 16 E-items in 5 groups across about 45 modules.
4. Yes, including the `tests/test_*.py` glob.
5. Yes. Deleting a rule emitter without its registry entry changes its severity to `error` (`check_engine._DEFAULT_RULESPEC`), and a deleted reader with a missed caller breaks a command.

AW-TIER: complex

### Step R1

- Checked: every symbol named in E-02 to E-12 by import and `hasattr` at HEAD. All exist except `prompts_index.run_find` (proofreading fix).
- `stale-index` counts per module match F-01 (check_engine 18, doctor 8, ipd_lifecycle 3, the three indexes 2 each, engine 1).
- `artifact_types.TYPE_BACKENDS` index entries are the three `run_index` functions. `cli._run_plans` has `if getattr(args, "write_index", False)` and no parser defines the flag. `plans.render_status_index` is used only by tests there.
- `check_engine.check_content` calls `plans_index.check_drift` and `research_index.check_drift` only under `include_retired`; `prompts_index.check_drift` is called only from `prompts_index.run_index` (PR-001, PR-002). Measured: `aw check all --agent` reports 0 `check.stale-index-*` findings, and `aw check all --all --agent` reports 2.
- `tools/gate_drop_audit.py` calls `check_engine._status_meta` and `backlog.parse_item` (PR-004).
- `dcerjg` E-09 computes `last_history_day` with `attention_contract.newest_history_record` (PR-005).
- `tests/test_runner_shared.py::CrossHostReadIdReExportTests` pins loose spellings through the host `_read_id` re-export of `selectors.read_front_matter_id` (PR-006).
- `artifact_audit.build_index` holds `_INDEX_CACHE` keyed by repo root and record types, as F-10 says.
- `tests/record_builder.py` does not exist yet; `59aiyh` creates it before this plan, as stated.
- No CI, Makefile or pre-commit file runs `aw index ... --check` (F-05 re-checked).

### Step R2

- Checked: the E/V bijection is 16/16.
- Baselines measured without `--all` would show no INDEX or F-04 content findings, so E-03 and V-03 could not show "equal except the stale-index ids" (PR-001).
- `/tmp` evidence is lost when the lane is integrated (PR-007). Count equality does not fit retargets that rename tests (PR-008).
- Reachability: V-02's alias line comes from E-02; V-04's producers test comes from E-04; V-13's sentinel test comes from E-13 through `cli.main`.
- Dependencies: `meta_cli.index_rebuild` (`1ajqaa` E-05) and `migrations/m0001_*` (`dcerjg`) were not guaranteed by the declared edges (PR-003).

### Step R3

- Checked: the plan deletes code and adds tests. No trust boundary changes. The pre-commit hooks keep their verdicts through the retargets that `t4gl15` already made. `aw sanitize --agent` runs in E-16.

### Step R4

- A: The `--check` compatibility of OQ-01 keeps a check a user may rely on.
- C: One owner (`artifact_meta`); no duplicate paths remain. A rule emitter and its registry entry are deleted together (E-05).
- D: The pin rule now detects dropped cases (PR-008). Every rule that `check_drift` hosts keeps a home (PR-002). External callers in `tools/` are found (PR-004).
- E: Two new core modules; retargets keep every input case.
- F: The alias prints one information line, with no silent change.
- Spec sync: "No spec change" is true. The plan implements 4.3, 4.5 and section 7 step 7 as written.

### Step R5

- Checked through the eight personas: QA (baselines on the right path), testing (no lost cases), UX (the alias line), architect (one owner), engineer (real symbols and callers), power user (`aw index plans --check` still gates content rules), novice (help strings updated), stakeholder (AC-1 and AC-9 phase-B forms, finished by `cxxmyv`).

### Step R6

- Checked: 16 E-items in 5 groups. E-12's size depends on F-20; OQ-03 now records a non-stopping follow-on path (PR-009). No split is recommended now (D-2).

### Step R7

- Checked `1ajqaa` E-05 (`index_rebuild`), `dcerjg` E-09 and its Scope-Paths (`m0001_*`), `xexn45` F-08 (the four adapters), `59aiyh` (the builder; this plan carries its "deleting production parsers" deferral), `ffceq0` (D-2 loose values, E-08 skip list) and `t4gl15` (the deletions it defers here), and `cxxmyv` E-04 (on-disk INDEX files, ignore lines and skip names). The two new dependency edges make the orchestrator `63ib9r` child-table row 11 (`executed:ffceq0`, `executed:t4gl15`, `executed:59aiyh`) list fewer edges than the plan. `63ib9r` is not in this review's ledger, so it was not edited; `aw ipd coverage 63ib9r` still reports ready. Recorded for the orchestrator's own review.

### Step S5

- Checked: OQ-01 to OQ-04 are resolved. OQ-05 is resolved from evidence (the two prerequisites' `- Item-Dependencies:` lines), with the reviewer as owner. No question needs the human.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R1 / R2 evidence | `check_engine.check_content` "if dirs and include_retired: drift.extend(_pidx.check_drift(...))"; measured 0 vs 2 `check.stale-index-*` with and without `--all` | Baselines and comparisons without `--all` never reach `check_drift`, so the INDEX-rule removal and the F-04 rule preservation were both unobservable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baselines and comparisons use `--all`. |
| PR-002 | MEDIUM | UNDER-SCOPE | R4 D | `prompts_index.check_drift` "name-metadata-mismatch"; its only caller is `prompts_index.run_index` | Once `run_index` became an alias, the prompts naming rule would have no caller. | Low | FIXED | E-02 wires it into the prompts branch of `check_content`, and V-02 tests it. |
| PR-003 | MEDIUM | IN-SCOPE | R2 dependencies | E-02 "`meta_cli.index_rebuild`"; E-10/E-14 `m0001`; `1ajqaa` and `dcerjg` "Item-Dependencies: executed:tve77h" | Two prerequisites were not reachable through the declared edges. | Low | FIXED | Added `executed:1ajqaa` and `executed:dcerjg`; OQ-05. |
| PR-004 | MEDIUM | UNDER-SCOPE | R1 | `tools/gate_drop_audit.py` "check_engine._status_meta(item_text)" and "backlog.parse_item(item_text)"; `tests/test_gate_drop_audit.py` | The plan searched only `agent_workflows`; deleting these symbols breaks a tested tool. | Low | FIXED | E-01 searches `tools/`; E-12 retargets; Scope-Paths and V-12 extended. |
| PR-005 | MEDIUM | IN-SCOPE | R7 | `dcerjg` E-09 "`last_history_day` from `attention_contract.newest_history_record`" | E-10 deletes the original that the migration calls. | Low | FIXED | The migration calls the moved function; migration tests are added to V-10. |
| PR-006 | MEDIUM | IN-SCOPE | R4 D | `tests/test_runner_shared.py::CrossHostReadIdReExportTests` | Deleting `read_front_matter_id` breaks the host `_read_id` loose-spelling contract. | Low | FIXED | Rebind to `read_text`'s loose `id`; the test passes unchanged. |
| PR-007 | MEDIUM | IN-SCOPE | R2 | E-01 "`/tmp/opencode/9o83cr-before/`"; E-14 exclusion file | Evidence outside the lane workspace is lost on integration. | Low | FIXED | `.aw/state/9o83cr/`; the exclusions are also copied into F-21. |
| PR-008 | LOW | IN-SCOPE | R2 | V-08 "equal passed counts" | Retargets rename tests, and counts alone cannot show that a case was kept. | Low | FIXED | PIN RULE outcome lists, with removed names mapped to their successors. |
| PR-009 | LOW | IN-SCOPE | S7 fence wording | OQ-03 "the executor stops after E-11" | A stop over a sizing question contradicts the runner's no-stranding rule. | Low | FIXED | Finish E-11, record follow-on rows, report. |
| PR-010 | MEDIUM | UNDER-SCOPE | S7 contract | Gate text | The gate lacked the honesty rule, the `git add -A` ban, the fence-as-declaration wording and conditional finalize ownership. | Low | FIXED | Full gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Add `executed:1ajqaa` and `executed:dcerjg`? | Yes | Rely on Set order | `1ajqaa` and `dcerjg` depend only on `tve77h`; E-02 and E-10 need their outputs | yes |
| D-2 | Split E-12 now? | No; follow-on rows if F-20 exceeds about 40 | Split now (the size is unknown until F-20) | OQ-03 | yes |
| D-3 | Keep the prompts naming rule? | Yes, through `check_content` | Drop it with `run_index` (silent loss) | F-04 spirit; OQ-01 | yes |
| D-4 | Edit the orchestrator's child table? | No; recorded for its review | Edit `63ib9r` (outside this ledger) | Plan-review Step 0.1 ledger rule | yes |

## Round 2

This re-review ran at HEAD `c42ce196a` in an isolated non-interactive runner review-sweep lane worktree. Approval had been withdrawn on 2026-11-07 per maintainer direction to pause before re-review while the metastore plans were re-split for the any-repo migration (`g5hpbb`). The tracked plan `.aw/records/plans/pending/20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned clean (0 errors, 0 warnings, 2 info IPD-C802). Baseline unit tests passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_executed_transition_gate.py tests/test_ipd_dependency_statement_gate.py` printed `29 passed in 1.05s`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned clean with 0 errors and 0 warnings (IPD-C802 cleared).

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` (retained `- Review-Depth: complex`) | PR-006 (MD-15, Section 7.2) |
| `## Workflow history` | Bullets from round-3 split and earlier rounds | Added newest-first review history entry with verdict and findings PR-001..PR-006 | PR-006 (MD-15, Section 7.2) |
| E-01 | Baseline capture without ensuring directory existence | Added explicit `mkdir -p .aw/state/9o83cr/before/` instruction into E-01 | PR-003 (Executability / R2) |
| `## Proposed changes` | Ordered list of 3 steps, no diagram | Ordered list of 4 steps plus Mermaid `flowchart TD` | PR-002 (Requirement 12b) |
| OQ-01..OQ-04 | `- Owner: none` | `- Owner: plan author` | PR-004 (`s5-questions.md:21`) |
| Line 211 | Two em dashes in reachability rule text | Replaced em dashes with parentheses | PR-005 (`IPD-C802`) |
| `## Approval and execution gate` | Lacked explicit safety stop for missing prerequisite split parts and scope fence production clarification | Added narrow safety stop for missing implementations from `0xsx2n`, `e8420v`, `k6jd6l`, `q6epwc`, `snin8q`, or `artifact_meta`, and clarified scope fence declaration | PR-001 (`s7-finalize.md:31-46`) |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Proves AC-1 single-owner and AC-9 deletion for the metastore C5 contract.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes.
3. Yes. Finishing audit plan of metastore with 4 E-items in 3 task groups across 45+ affected modules.
4. Yes. `- Scope-Paths:` explicitly declares `tests/test_metadata_single_owner.py` and the plan itself.
5. Yes. Proves complete removal of legacy parsers and single-owner enforcement.

AW-TIER: complex

### Step R1

- Checked: target test module `tests/test_metadata_single_owner.py` declared in `- Scope-Paths:`; governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (C5, Section 4.3, Section 4.5, AC-1, AC-9); upstream split plans `0xsx2n`, `e8420v`, `k6jd6l`, `q6epwc`, `snin8q`, and prerequisite plans `ffceq0`, `t4gl15`, `59aiyh`, `1ajqaa`, `dcerjg`, `g5hpbb`, and `clors0` in `- Item-Dependencies:`.
- Verified that all symbols and callers referenced in E-01, E-13, and E-14 are correctly accounted for across the split parts.

### Step R2

- Checked: 1:1 bijection between E-items (E-01, E-13, E-14, E-16) and V-items (V-01, V-13, V-14, V-16); `- Scope-Paths:` completeness; `- Item-Dependencies:` completeness; and verification reachability.
- Confirmed that baseline capture in E-01 has explicit directory creation instruction (`mkdir -p .aw/state/9o83cr/before/`).

### Step R3

- Checked: isolation and hygiene. The plan authors a behavioral test module and runs non-modifying audit scans. No secrets or network paths involved.

### Step R4

- Checked: right-sizing, anti-regression, and conceptual density.
- Sized cleanly (4 items in 3 task groups) as the finishing proof and validation plan of the metastore migration.

### Step R5

- Checked through all eight personas: QA (clean baseline and multiset verification), testing (behavioral single-owner test with no AST/inspect code pinning), UI/UX (alias messaging preserved), architect (C5 single reader/writer invariant proved), engineer (executable path-scoped plan), power user (index aliases maintained), novice (clear error exits when unpatched), stakeholder (AC-1 and AC-9 verified).

### Step R6

- Checked: decomposition and splitting. The plan was split in round 3 to allocate deletion work into five child plans (`q6epwc`, `snin8q`, `k6jd6l`, `e8420v`, `0xsx2n`), leaving this plan sized cleanly for residual audit, single-owner proof, and finish. No further split needed.

### Step R7

- Checked consistency across all metastore plans and Order 00 orchestrator. Prerequisites correctly reflect all split parts and migration ordering dependencies.

### Step S5

- Checked: OQ-01 through OQ-05 are resolved, non-blocking, and owners updated from `none` to `plan author`. Review decisions (D-1..D-5) recorded and verified (`Reversible: yes`).

### Pass 2

- Re-read all revised sections of `9o83cr`. Confirmed exact 1:1 E/V mapping, valid Mermaid diagram, zero em or en dashes, and verified `aw ipd lint --phase review-finalize --agent` returned clean (0 errors, 0 warnings).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | `.aw/records/plans/pending/20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.ipd.md:234-245`; `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46` | The gate lacked a narrow safety stop for missing prerequisite split parts or `artifact_meta` implementations, and needed scope fence clarification that production code is not modified by this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added narrow unsafe-condition prerequisite stop and clarified scope fence in the execution gate (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / R6 | `.aw/records/plans/pending/20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.ipd.md:107-111`; `.aw/system/workflows/technical-writing/technical-writing.md:40-46` | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for a multi-step audit and verification process. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added ordered 4-step process and Mermaid `flowchart TD` diagram to `Proposed changes` (strong). |
| PR-003 | LOW | IN-SCOPE | Executability / R2 | `.aw/records/plans/pending/20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.ipd.md:48` | E-01 instructed saving baseline outputs to `.aw/state/9o83cr/before/` without ensuring directory creation, risking shell redirect failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/9o83cr/before/` instruction into E-01 (strong). |
| PR-004 | LOW | IN-SCOPE | S5 / IPD Schema | `.aw/records/plans/pending/20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.ipd.md:174, 181, 188, 202`; `.aw/system/workflows/plan-review/steps/s5-questions.md:21` | OQ-01, OQ-02, OQ-03, and OQ-04 had `- Owner: none` rather than naming an accountable owner (`plan author`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated OQ-01, OQ-02, OQ-03, and OQ-04 owner from `none` to `plan author` (strong). |
| PR-005 | LOW | IN-SCOPE | Proofreading / Prose Style | `.aw/records/plans/pending/20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.ipd.md:211`; `AGENTS.md`; `IPD-C802` | Line 211 contained two em dashes in reachability rule text, triggering `IPD-C802` lint advisories. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced em dashes with parentheses, clearing `IPD-C802` (strong). |
| PR-006 | MEDIUM | IN-SCOPE | Front Matter / Lifecycle | `.aw/records/plans/pending/20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.ipd.md:9`; `.aw/system/workflows/plan-review/steps/s7-finalize.md:3-6` | Front matter was at `- Status: to-review` and lacked required `- Readiness:` field. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Advanced `- Status: reviewed`, added `- Readiness: go-pending-approval` to front matter, and prepended newest-first review entry to `## Workflow history` (strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the plan execution gate specify safety stops and scope fence? | Add narrow safety stop if prerequisite modules from `0xsx2n`, `e8420v`, `k6jd6l`, `q6epwc`, `snin8q`, or `artifact_meta` are absent, and clarify scope fence declaration that production code is not modified | Omit safety stop | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46` | yes |
| D-2 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add ordered 4-step process and Mermaid `flowchart TD` in `Proposed changes` illustrating baseline capture, single-owner test authoring, AC-1 audit, and full validation pipeline | Omit diagram (violates Requirement 12b) | `.aw/system/workflows/technical-writing/technical-writing.md:40-46` Requirement 12 | yes |
| D-3 | How should baseline directory creation be handled? | Add explicit `mkdir -p .aw/state/9o83cr/before/` into E-01 | Rely on implicit existence | `.aw/system/workflows/plan-review/steps/r2-executability.md` | yes |
| D-4 | How should OQ-01..OQ-04 owners be recorded? | Update `- Owner: none` to `- Owner: plan author` to satisfy open question ownership requirements | Leave `none` | `.aw/system/workflows/plan-review/steps/s5-questions.md:21` | yes |
| D-5 | What review depth and readiness should be recorded in front matter? | Retain `- Review-Depth: complex` (Order 11 complex finishing audit plan spanning AC-1 and AC-9 proofs) and set `- Readiness: go-pending-approval` with `- Status: reviewed` | Demote to standard; leave readiness absent or no-go | `.aw/system/workflows/plan-review/steps/t-tier.md`; `.aw/system/workflows/plan-review/steps/s7-finalize.md:3-6, 61-78` | yes |
