# Review findings: ipd epsj2v

- Subject-Id: epsj2v
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261122T000435Z-1280895`). The target plan `.aw/records/plans/pending/20261121-dswbr8-01-epsj2v-skip-legacy-agents-non-record-directories-in-attention-fallb.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `2` `IPD-C802` info advisories on line 148). Inspection of backlog item `dswbr8`, `agent_workflows/attention.py`, `agent_workflows/attention_contract.py`, `agent_workflows/artifact_core.py`, `agent_workflows/project_context.py`, `agent_workflows/layout_inventory.py`, `agent_workflows/migrations/chain.py`, `agent_workflows/migrations/m0001_discover.py`, `agent_workflows/manifest.py`, and `tests/test_attention_blind_spot.py` surfaced two `LOW` findings (`PR-001..PR-002`), both fixed in place. Pass 2 re-checked `Scope`, `Goal`, `E-01..E-03`, `Step 0`, `Findings`, `Proposed changes`, the Mermaid flowchart, `Scope check`, `V-01..V-03`, and `Approval and execution gate` for full internal consistency.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Validation and cross-check`, `Approval and execution gate` (`COMMIT`) | Line 148 contained two `IPD-C802` em dashes and `COMMIT` omitted the shared-checkout safety clause | Replaced em dashes with parentheses for zero lint diagnostics and added the shared-checkout safety clause to `COMMIT` | PR-001, `steps/p-proofread.md`, `steps/s7-finalize.md` |
| `E-02` item 1 | Invoked `cli.main(["att", ...])` and `cli.main(["attention", ...])` without stdout/stderr capture or checking that `VIEW INVALID` is absent from `aw att` output | Added `contextlib.redirect_stdout`/`redirect_stderr` capture and explicit assertion that `VIEW INVALID` is absent from `aw att` output | PR-002, `steps/r4-engineering.md` |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes; updates the fail-closed `attention.uninventoried-tree` discovery behavior of `agent_workflows/attention.py::scan` and `aw att` / `aw attention --check` for legacy `.agents/` repositories.
2. No; touches only read-only tree discovery in `agent_workflows/attention.py` and behavioral tests in `tests/test_attention_blind_spot.py`.
3. No; small, cohesive bug fix (`3` E-items in `2` task groups across `1` production file and `1` test file).
4. Yes; `- Scope-Paths:` explicitly lists `agent_workflows/attention.py` and `tests/test_attention_blind_spot.py`.
5. Yes; `attention.py::scan` backs the `aw attention --check` CI gate, so an overly broad exemption (such as adding non-record directories to `TREE_POLICY` or skipping them under `.aw/records/`) would silently reopen the `1qt1u3` blind spot.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261121-dswbr8-01-dswbr8-attention-legacy-agents-workflows-uninventoried.backlog.md`, `agent_workflows/attention.py` (imports including `FrozenSet`, `_classify_tree`, `scan`, `render_json`, `resolve_excluded_tree_matches`), `agent_workflows/attention_contract.py` (`TREE_POLICY`, `is_nonartifact_name`), `agent_workflows/artifact_core.py` (`DEFAULT_IGNORED_DIR_NAMES`, `is_ignored_path`), `agent_workflows/project_context.py` (`project_records_dir`), `agent_workflows/layout_inventory.py` (`classify_item`), `agent_workflows/migrations/chain.py` (`_AGENTS_NON_RECORD_TOP_DIRS`), `agent_workflows/migrations/m0001_discover.py` (`AGENTS_NON_RECORD_TOP_DIRS`), `agent_workflows/manifest.py` (`LEGACY_MANIFEST_RELPATH`), and `tests/test_attention_blind_spot.py`.
- Verified every symbol, directory list, and behavior claim resolves accurately: `DEFAULT_IGNORED_DIR_NAMES` contains `".aw/records/runs"` (confirming `E-02` item 3), `project_records_dir` returns `repo / ".aw" / "records"` when no stored policy exists (triggering the `.agents` fallback on legacy repos and modern pre-records installs), and the six names (`workflows`, `skills`, `agent-workflows`, `inbox`, `runs`, `state`) cover every non-record top-level directory under `.agents/` in `layout_inventory.py::classify_item`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`3/3`: `E-01..E-03` <-> `V-01..V-03`, `- Highest E allocated: 03`), dependency chain (`E-01 -> E-02 -> E-03`), `- Scope-Paths:` completeness (`2` files), `- Item-Dependencies: none`, runtime reachability of `V-01..V-03` (all demand git diffs, pytest runs, or `rg` checks reachable by construction), and `Approval and execution gate` (resolved OQ precondition, non-stopping scope fence with `--scope-reason`/`--scope-ack`, hard-MUST honesty rule, path-scoped `aw commit epsj2v`, conditional runner/executor `aw ipd finalize epsj2v` ownership).
- Added the shared-checkout safety clause to `COMMIT` (`PR-001`).

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). `attention.py::scan` is strictly read-only, writes nothing to disk, and scopes `_LEGACY_AGENTS_NON_RECORD_DIRS` strictly to the fallback branch when `project_records_dir(repo_root)` does not exist on disk, preventing unintended exemption of unrecognized directories under `.aw/records/` or `.agents/`.

### Step R4

- Checked: correctness and data integrity (verified `_classify_tree` maps `.aw/records/<tail>` onto `.agents/<tail>`, confirming `TREE_POLICY` must remain unchanged and the skip must be gated on `using_legacy_agents_fallback`), anti-regression and testing (`E-02` pins legacy 1.2.1 acceptance, legacy co-existence with unknown `.agents/newtype`, modern `.aw/records/` flagging of all five non-ignored names while `.aw/records/runs` stays ignored, and modern pre-records `.aw/system/` + `.agents/skills/` installs; strengthened `E-02` item 1 with stdout/stderr capture and explicit `VIEW INVALID` absence check in `PR-002`), right-sizing (`3` E-items, `2` Scope-Paths, cohesive single-concern fix), and `## Spec / documentation sync` (`N/A` verified truthful).

### Step S5

- Checked: `## Open questions` (`OQ-01`, `Status: resolved`, `Blocking: no`, `Owner: plan author`, grounded in verified repository evidence across five modules and direct reproduction `F-02`) and `Deferred / out of scope` (both entries carry valid `Carrier-Declined` rationales). Both review findings (`PR-001..PR-002`) have `Overall:Low` Remediation Risk and are fixed directly; no review-level design decisions were needed beyond these editorial/hygiene fixes. Zero blocking or human-owned questions remain.

### Pass 2

- Re-checked the complete revised plan across `Scope`, `Goal`, `E-01..E-03`, `Step 0`, `Findings`, `Proposed changes`, the Mermaid flowchart, `Scope check`, `Required tests / validation`, `Spec / documentation sync`, `Open questions`, `V-01..V-03`, and `Approval and execution gate`.
- Verified `3/3` E/V bijection, `- Highest E allocated: 03`, zero unresolved questions, and clean `aw ipd lint --phase review-finalize --agent` disposition with `0` diagnostics.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | LOW | IN-SCOPE | Proofreading / S7 / Lint diagnostics and gate completeness | .aw/records/plans/pending/20261121-dswbr8-01-epsj2v-skip-legacy-agents-non-record-directories-in-attention-fallb.ipd.md:148,174 | Line 148 contained two em dashes flagged by `IPD-C802`, and `Approval and execution gate` (`COMMIT`) omitted the shared-checkout safety clause forbidding altering, reverting, staging, or committing unrelated concurrent changes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced em dashes on line 148 with parentheses so `aw ipd lint --phase review-finalize --agent` reports `0` diagnostics, and added the shared-checkout safety clause to `COMMIT`. Recommendation strength: strong. |
| PR-002 | LOW | IN-SCOPE | R2 / R4 / CLI test stdout isolation and symptom assertion | .aw/records/plans/pending/20261121-dswbr8-01-epsj2v-skip-legacy-agents-non-record-directories-in-attention-fallb.ipd.md:50; .aw/records/backlog/graduated/20261121-dswbr8-01-dswbr8-attention-legacy-agents-workflows-uninventoried.backlog.md:19-24 | `E-02` item 1 invoked `cli.main(["att", ...])` and `cli.main(["attention", ...])` inside `unittest.TestCase` without capturing stdout/stderr or asserting that `VIEW INVALID` (the exact symptom in backlog `dswbr8`) is absent from `aw att` output. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-02` item 1 to capture stdout/stderr via `contextlib.redirect_stdout`/`redirect_stderr` and assert both exit `0` and that `VIEW INVALID` is absent from `aw att` output. Recommendation strength: medium. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| (none) | | | | | |
