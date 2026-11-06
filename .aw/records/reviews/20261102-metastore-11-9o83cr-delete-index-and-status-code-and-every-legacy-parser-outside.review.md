# Review findings: plan 9o83cr

- Subject-Id: 9o83cr
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
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
