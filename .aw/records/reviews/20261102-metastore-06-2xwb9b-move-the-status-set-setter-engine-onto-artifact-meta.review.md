# Review findings: plan 2xwb9b

- Subject-Id: 2xwb9b
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `332e5f15f` in a runner review-sweep lane worktree (non-interactive). The lane-input
copy (revision 5) is byte-identical to the tracked plan, which was committed and unmodified, so no
pre-review snapshot was needed. `aw ipd lint --phase author` reported clean.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-03, V-03 | `_storage_format(records_root)` returns `legacy` until Order 13 | Per-target rule: `log` when `meta/<id6>.jsonl` exists, else `legacy`; tve77h's write module must still pass | PR-001. |
| E-12, V-12 | Three callers of `review_attestation_missing` | Four, including `runner_shared.reconcile_disposition`, with the lane-worktree root and uncommitted-bytes requirement; `tests/test_spec_review_dispatch.py` added | PR-002. |
| E-11 | All text-taking signatures change to `State` | `_format_status_transition_line` keeps its signature (a test calls it directly) | PR-003. |
| E-01, E-10, E-15, V-01, V-10, V-15 | Dumps under `/tmp/opencode`; `aw check` "pre-E-01 baseline" never captured | Dumps and an `aw check --agent` baseline under `.aw/state/2xwb9b/`; `(location, rule)` diff | PR-004. |
| Gate | Partial execution contract | Full contract | PR-005. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: it changes the `->reviewed` attestation contract (SR-601) and the `artifact_meta.append` interface that Orders 07 to 13 depend on.
2. Partly: it routes every setter write and its staged `git mv` through new code; no guard module is edited.
3. Yes: 15 E-items in 5 task groups, the 4,585-line setter engine plus `artifact_meta` and `review_findings`.
4. Yes: 7 Scope-Paths.
5. Yes: every status change in the toolkit passes through this code; a byte drift corrupts records silently, which is why the plan pins bytes first.

AW-TIER: complex

### Step R1

- Checked in this lane: `status_set.py` is 4,585 lines (plan: 4,571 at `0cbfcc706`; drift only); `rg "re\.(compile|match|search|finditer|split)"` gives 21 lines (plan F-01: 20; same patterns, drift only), all metadata; module-level `_ID_RE`, `_STATUS_RE`, `_SET_RE`, `_HISTORY_HDR_RE`, `_GATE_KIND_RE`, `_GATE_REF_RE`, `_GATE_SUMMARY_RE` present; `atomic_write`, `git_mv`, `record_history` and `orch.path.write_text` call sites at the lines E-08/E-09 target, plus one comment mentioning `artifact_core.git_mv` near `offer_commit` (V-08's `rg` would print that comment line; the executor must paste it and note it is a comment, or reword the comment; no finding raised because V-08's intent is clear); every one of the 28 baseline test modules exists; `review_findings.review_attestation_missing` accepts any parseable, correctly typed record and never reads the verdict (SR-601 premise holds); 24 `specflow` refinement review files exist and no code in `agent_workflows/` or `.aw/system/workflows/` writes refinement verdicts today, so E-12's `review_kind` inference (tve77h E-12: `specflow` refinement files are `refinement`) covers the whole population.
- Callers of `review_attestation_missing`: `specs._review_attestation_refusal`, `check_engine.check_spec_review_attestation`, the positional path in `status_set` (through `specs._review_attestation_refusal`), and `runner_shared.reconcile_disposition` (missed by the plan; PR-002).
- `_format_status_transition_line` is called directly by `tests/test_blocks_release_reader_bounding.py` with an `ArtifactRecord`; `plan_priority_work_kind_problems` and `read_item_dependencies_value` have only in-module callers (PR-003).

### Step R2

- Checked: E/V bijection 15/15; each V demands named test runs, pasted diffs or dumps; reachability by construction. Scope-Paths cover the edits; `tests/test_spec_review_dispatch.py` and `tests/test_artifact_meta_write.py` are only RUN, not edited. `- Item-Dependencies: executed:tve77h, executed:7ehv8l` is correct (`7ehv8l` re-points the `2vev8j` citations in `status_set.py` comments first, avoiding an edit conflict on the same file). The `aw check` baseline E-15 compared against was never captured (PR-004).

### Step R3

- Checked: the setter's message leak refusal (F-08, via tve77h E-03) is a deliberate stricter behavior; the attestation predicate is a security-relevant gate (it licenses `reviewed`, which precedes approval), and making it stricter is fail-closed. No secret or input-validation regression. No finding beyond PR-002, which concerns that gate's correctness in lanes.

### Step R4

- Checked: A, the legacy write order keeps today's move-then-write (F-07) and failure-before-content-write semantics (`tests/test_history_write_order.py`); the freshness digest check prevents a lost update between read and write. C, reuses `releases.set_*_line`, `backlog.set_*_line`, `record_placement`, `artifact_core.git_mv`, `platform_lock`. D, 28 W/R rows map every moved behavior to a test, and E-02 pins the NEW ones before the change. E, cache-state parity (E-14), dry-run, batch refusal and companion cases present. F, the repository-wide `legacy` switch would route tve77h's own log-branch tests (`tests/test_artifact_meta_write.py`, its E-15 failure injection and E-16 repair) to the legacy branch at this merge and fail the core tier, contrary to C10a and AC-1b (PR-001).

### Step R5

- Checked through the eight personas: QA and regression are strongly covered by the byte pins; architect: the per-target format rule gives one dispatch point that Order 13 replaces; engineer: `LegacyRender` and `WritePreview` are defined and their removal is carried by `cxxmyv`; power user: no CLI change except the two deliberate stricter refusals (F-08, E-12), documented by Order 12; novice: refusal text for refinement-only specs names `/spec-review`; stakeholder: AC-15, AC-14a and AC-31 phase-B ownership consistent with the orchestrator. No further finding.

### Step R6

- Checked: 15 E-items, 5 groups. OQ-01 records the seam (Task group 4) and argues against splitting; each E-item is one concern. No split recommended (D-2).

### Step R7

- Checked: `tve77h` E-13/E-15 interface names (`append(id6, events, *, expect_seq)`, `resolve`, `read`, `query`, `validate_new_events`) used consistently; `tve77h` E-15 tests call `append` on synthetic logs in temporary repositories, which motivated PR-001; `1ajqaa` was revised in its own review to write fixture logs directly, so it is unaffected either way; `xexn45` E-01 routes the phase-B branch of `create`/`append` through `write_legacy`, consistent with the per-target dispatch; `cxxmyv` E-03 deletes this legacy branch and `LegacyRender`, as the Deferred row states; `t4gl15` owns the HEAD-status read (Deferred, consistent); OQ-02 answer matches `cxxmyv` OQ-01 and spec 4.2 `overrides` (amended 2026-11-05).

### Step S5

- Checked: OQ-01 to OQ-04 resolved and non-blocking; OQ-02 carries `Owner: maintainer` and cites the maintainer's /askme answer recorded in `cxxmyv` OQ-01 (verified there). No new human question.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R4 F / R7 C10a | plan E-03 "`_storage_format(records_root)` returning `legacy` until Order 13"; `tve77h` E-15 "used by tests now" with failure injection in `tests/test_artifact_meta_write.py` | A repository-wide `legacy` dispatch sends tve77h's merged log-branch write and repair tests through the legacy branch. They fail, or stop testing the log path, at this merge, which breaks the per-merge core gate (AC-1b). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Per-target rule: `log` when `meta/<id6>.jsonl` exists, else `legacy`. E-01 and V-03 run the tve77h module and compare counts; a test checks both branches. |
| PR-002 | MEDIUM | UNDER-SCOPE | R1 callers / R3 gate | `runner_shared.reconcile_disposition` calls `review_findings.review_attestation_missing(source, id6, "spec")` with a lane root and uncommitted files | E-12 named three callers and missed the runner's spec-review disposition gate. A cache keyed to the wrong root, or a freshness check that ignored uncommitted bytes, would fail every correct runner spec review. | Low | FIXED | E-12 names the fourth caller and its root and working-bytes requirement; `tests/test_spec_review_dispatch.py` is added to E-12, V-12 and the baseline. |
| PR-003 | LOW | IN-SCOPE | R4 D regression | `tests/test_blocks_release_reader_bounding.py` calls `status_set._format_status_transition_line(rec1, rec1.path, ...)` | E-11 changed "the text-taking signatures" to `State`, which could break a test that the plan says must pass unchanged. | Low | FIXED | `_format_status_transition_line` keeps its signature; only the two in-module-only functions change. |
| PR-004 | MEDIUM | IN-SCOPE | G executability | E-01 "`/tmp/opencode/2xwb9b-inventory-before.json`"; E-15 "against a pre-E-01 baseline" | The dumps were written outside the lane workspace, and no item captured the `aw check` baseline. | Low | FIXED | Dumps and the baseline are saved under `.aw/state/2xwb9b/`; V-15 diffs `(location, rule)` pairs. |
| PR-005 | MEDIUM | UNDER-SCOPE | S7 execution contract | plan gate | The gate was missing the honesty rule, the `git add -A` ban, the declaration wording, conditional finalize ownership and the dependency precondition. | Low | FIXED | Gate rewritten. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does `append` pick its format in phase B? | Per target: `log` if its `meta/<id6>.jsonl` exists, else `legacy` | Repository-wide constant (breaks tve77h tests); explicit `format=` argument at every call site (pushes the decision to every caller) | tve77h E-15 tests; C10a; tve77h E-13 loader already reads a log when one exists | yes |
| D-2 | Split Task group 4 into its own child? | No | Split at the OQ-01 seam | OQ-01 rationale; each E-item is one concern | yes |
