# Review findings: ipd acqenf

- Subject-Id: acqenf
- Subject-Type: ipd
- Reviewed-At: 2026-11-19
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261119T170610Z-99310`). The target plan `.aw/records/plans/pending/20261119-xxdzcq-01-acqenf-preserve-prompt-kind-and-created-day-in-artifact-meta-load-l.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` errors, `0` warnings, `2` `IPD-C802` info advisories on the standard Validation boilerplate). Inspection of backlog item `xxdzcq`, `agent_workflows/artifact_meta.py`, `agent_workflows/prompts.py`, `agent_workflows/migrations/m0001_convert.py`, `agent_workflows/cli.py`, and the test suite (`tests/test_artifact_meta_legacy.py`, `tests/test_artifact_meta_legacy_writer.py`, `tests/test_artifact_meta_loader_parity.py`, `tests/test_prompts_new.py`) surfaced one `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-003`), all fixed in place. Pass 2 re-checked `E-01..E-03`, `V-01..V-03`, `OQ-01`, the Mermaid diagram, and the Approval and execution gate, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean`.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `E-02` (line 51) | Used `meta.read`, `meta.create`, `cli.main` and described stale `.aw/state/index.db` as "missing those prompt columns" | Cited `agent_workflows/artifact_meta.py::read`, `agent_workflows/artifact_meta.py::create`, `agent_workflows/cli.py::main` and described stale rows as having `NULL` `prompt_kind` and `created_day` values under an older `schema_hash` | PR-003, `steps/p-proofread.md` Section 11.1 |
| `Proposed changes` Mermaid diagram | `D -->|backlog and Kind| E["target_k = work_kind (unless Work-Kind set)"]` with unconditional `E --> H` | Clarified `E["If Work-Kind set, skip Kind; else target_k = work_kind"]` and edge `E -->|when Work-Kind absent| H` | PR-003, technical writing standard Requirement 12(d) |
| `Open questions` (`OQ-01`) | `- Owner: none` on resolved question | Updated to `- Owner: plan author` | PR-002, `steps/s5-questions.md` |
| `Approval and execution gate` | Unconditionally instructed `aw ipd finalize acqenf` and omitted honesty, scope-fence variance, resolved-OQ, and hand-`git mv` clauses | Added `OQ-01` resolved precondition, `--scope-reason`/`--scope-ack` scope-fence rule, hard-MUST paste-runner-output honesty rule, hand-`git mv` prohibition, and conditional runner/executor finalize ownership | PR-001, `steps/r2-executability.md`, `steps/s7-finalize.md` |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No public CLI flag or file format changes; the change repairs `agent_workflows/artifact_meta.py::load_legacy_artifact` and bumps `LEGACY_LOADER_VERSION` so `artifact_meta.read` and `artifact_meta.query` return the declared `prompt_kind` and `created_day` values in `State` and the SQLite cache.
2. No; it does not touch private-data guards, commit helpers, worktree isolation, or sandbox boundaries.
3. No; it is small (`3` E-items across `2` task groups, `1` production file and `2` test files).
4. Yes; `- Scope-Paths:` lists `agent_workflows/artifact_meta.py`, `tests/test_artifact_meta_legacy.py`, `tests/test_artifact_meta_legacy_writer.py`, and the IPD itself.
5. Yes; `load_legacy_artifact` populates cache rows for every legacy artifact type (`ipd`, `spec`, `backlog`, `research`, `release`, `prompt`, `walkthrough`, `roadmap`), and `LEGACY_LOADER_VERSION` triggers repository-wide `.aw/state/index.db` rebuilds, so a branching mistake could regress non-prompt records.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261118-xxdzcq-01-xxdzcq-artifact-meta-load-legacy-artifact-drops-prompt-ki.backlog.md`, `agent_workflows/artifact_meta.py` (`REGISTRY["prompt"]`, `_COMMON_FIELDS`, `replay`, `LEGACY_LOADER_VERSION`, `compute_schema_hash`, `load_legacy_artifact`, `_store_legacy_artifact_projection`, `read`, `read_text`, `query`, `_PROMPT_COMMENT_KEY`, `_render_create_fields`, `create`), `agent_workflows/prompts.py::run_new`, `agent_workflows/migrations/m0001_convert.py::prompt_map`, `agent_workflows/cli.py::main`, and `tests/test_artifact_meta_legacy.py`, `tests/test_artifact_meta_legacy_writer.py`, `tests/test_artifact_meta_loader_parity.py`, `tests/test_prompts_new.py`, `tests/record_builder.py`.
- Confirmed all cited symbols exist and match the stated findings, except `E-02` used shorthand module names (`meta.read`, `meta.create`, `cli.main`) and imprecisely described stale cache rows as missing DDL columns (`PR-003`).

### Step R2

- Checked: `E-*`/`V-*` bijection (`3/3`: `E-01..E-03` <-> `V-01..V-03`, `- Highest E allocated: 03`), dependency chain (`E-01 -> E-02 -> E-03`), `- Scope-Paths:` completeness, `- Item-Dependencies: none`, runtime reachability of `V-01..V-03`, and the `Approval and execution gate`.
- Found missing/non-conforming execution contract clauses in `Approval and execution gate` (`PR-001`): unconditional `aw ipd finalize` instruction, missing hand-`git mv` prohibition, missing paste-actual-output honesty rule, and missing `--scope-reason`/`--scope-ack` scope-fence clause. Fixed in place.

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). `load_legacy_artifact` parses local repository markdown metadata into SQLite; it introduces no new trust boundaries, credentials, network calls, or unvalidated command invocations, and bumping `LEGACY_LOADER_VERSION` safely rebuilds local `.aw/state/index.db` caches without losing durable markdown records.

### Step R4

- Checked: correctness (`E-01` preserves non-prompt `Kind`/`kind` mappings and `backlog` `Work-Kind` precedence while setting `artifact_row["created_day"]` for prompts only to match `replay`), anti-regression (tested across `ipd`, `backlog`, `research`, and `test_tracked_corpus_five_type_byte_identity_round_trip`), right-sizing (`3` E-items, `4` Scope-Paths, single cohesive bugfix), and `## Spec / documentation sync` (`N/A` accurately reflects restoring existing `REGISTRY["prompt"]` contract without CLI/spec changes).

### Step S5

- Checked: `OQ-01` (`Blocking: no`, `Status: resolved`). Found `- Owner: none` (`PR-002`); updated to `- Owner: plan author` and recorded decision `D-1` in `### Decisions`. Zero human-owned or blocking questions remain.

### Pass 2

- Re-checked `E-01..E-03`, `V-01..V-03`, `OQ-01`, Mermaid diagram, and `Approval and execution gate` after revisions.
- Confirmed `3/3` bijection, `- Highest E allocated: 03`, zero unresolved questions, and clean `aw ipd lint --phase review-finalize --agent --verbose` disposition.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261119-xxdzcq-01-acqenf-preserve-prompt-kind-and-created-day-in-artifact-meta-load-l.ipd.md:164 | Approval and execution gate unconditionally instructed executing `aw ipd finalize acqenf` and omitted the explicit hand-`git mv` prohibition, paste-runner-output honesty rule, resolved-OQ precondition, and `--scope-reason`/`--scope-ack` scope-fence variance rule required by `steps/r2-executability.md` and `steps/s7-finalize.md`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` to require resolved `OQ-01`, `--scope-reason`/`--scope-ack` scope variance justification, pasting actual runner output, no hand-`git mv`, and conditional runner/executor finalize ownership. Recommendation strength: very strong. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261119-xxdzcq-01-acqenf-preserve-prompt-kind-and-created-day-in-artifact-meta-load-l.ipd.md:137 | `OQ-01` recorded `- Owner: none` on a resolved question, violating `steps/s5-questions.md`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `OQ-01` to `- Owner: plan author` and recorded decision `D-1` in `### Decisions`. Recommendation strength: very strong. |
| PR-003 | LOW | IN-SCOPE | Proofreading / R1 / Technical writing standard Requirement 12(d) | .aw/records/plans/pending/20261119-xxdzcq-01-acqenf-preserve-prompt-kind-and-created-day-in-artifact-meta-load-l.ipd.md:51 | `E-02` used shorthand module names (`meta.read`, `meta.create`, `cli.main`) and stated stale `.aw/state/index.db` caches are "missing those prompt columns" when those DDL columns already exist with `NULL` values, and the Mermaid diagram did not show `backlog` `Kind` being skipped when `Work-Kind` is present. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Qualified symbol citations to `agent_workflows/artifact_meta.py::read`, `agent_workflows/artifact_meta.py::create`, and `agent_workflows/cli.py::main`, corrected stale-cache wording to `NULL` values under an older `schema_hash`, and updated Mermaid node `E` and its outgoing edge. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should `load_legacy_artifact` set top-level `artifact_row["created_day"]` for prompts in addition to `artifact_row["fields"]["created_day"]`? | Yes, set `artifact_row["created_day"]` to `mapped_fields.get("created_day")` when `art_type == "prompt"`, and keep `None` for other record types. | Leave `artifact_row["created_day"]` as `None` for prompts (rejected: diverges from `agent_workflows/artifact_meta.py::replay:1586`, where `State.created_day` is populated from `current_fields.get("created_day")`, and leaves `artifact_meta.query` without `created_day` for prompts). | `acqenf` `OQ-01`, `agent_workflows/artifact_meta.py::replay:1586`, backlog `xxdzcq` | yes |
