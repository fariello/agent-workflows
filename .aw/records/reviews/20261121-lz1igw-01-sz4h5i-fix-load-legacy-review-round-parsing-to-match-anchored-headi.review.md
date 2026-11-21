# Review findings: ipd sz4h5i

- Subject-Id: sz4h5i
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261121T064614Z-2150223`). The target plan `.aw/records/plans/pending/20261119-lz1igw-01-sz4h5i-fix-load-legacy-review-round-parsing-to-match-anchored-headi.ipd.md` was committed and unchanged, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `2` non-blocking `IPD-C802` info advisories on template boilerplate). Inspection of backlog `lz1igw`, artifact metadata store spec `4sd62s` (`Sections 4.1a K5a`, `4.6`, `4.9.1`), `agent_workflows/artifact_meta.py`, `agent_workflows/meta_cli.py`, `agent_workflows/review_findings.py`, `agent_workflows/migrations/m0001_convert.py`, `tests/test_artifact_meta_legacy.py`, `tests/test_show_history.py`, `tests/test_check_meta.py`, `CHANGELOG.md`, and live corpus scan of `.aw/records/reviews/` surfaced one `BLOCKER`, two `HIGH`, and one `LOW` finding (`PR-001..PR-004`), all fixed in place. Because `E-04`/`V-04` were added (shifting `CHANGELOG`/gates to `E-05`/`V-05`) and `- Scope-Paths:` changed, Pass 2 re-reviewed the entire revised plan for internal consistency, E/V bijection (`5/5`), `- Highest E allocated: 05`, and clean `aw ipd lint --phase review-finalize --agent` disposition.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Concern`, `Scope`, `Scope-Paths`, `Goal`, `E-04`/`V-04`, `E-05`/`V-05`, `F-04`, `Proposed changes`, `Scope check`, `Required tests / validation`, `Spec / documentation sync` | Modified only `agent_workflows/artifact_meta.py` and omitted `agent_workflows/meta_cli.py::check_meta` (which also uses unanchored `_ROUND_HEADING_RE`) and `tests/test_check_meta.py::test_drift_review_rounds` (core-tier test that relied on `load_legacy_review` synthesizing `[1, 2, 3]` for sparse `[1, 3]`) | Added `agent_workflows/meta_cli.py` and `tests/test_check_meta.py` to `- Scope-Paths:`, added `E-04`/`V-04` aligning `check_meta` with `review_findings.parse_review_text` and updating `test_drift_review_rounds` (shifting `CHANGELOG`/gates to `E-05`/`V-05` and updating `- Highest E allocated: 05`) | PR-001, PR-002, `steps/r4-engineering.md` |
| `Approval and execution gate` | Single paragraph with ambiguous "through `aw ipd finalize sz4h5i` (or runner self-finalize)" and missing preconditions, `--scope-reason`/`--scope-ack`, shared-checkout safety, explicit hand-`git mv` prohibition, and post-finalization backlog `lz1igw` closure | Structured bulleted execution contract covering all required clauses and conditional runner/executor `aw ipd finalize sz4h5i` ownership | PR-003, `steps/r2-executability.md`, `steps/s7-finalize.md` |
| `E-02`, `E-05`, `F-01..F-03`, `Scope check`, `Spec / documentation sync`, `V-05` | Cited drifted live count `1,516` as a bare fact, truncated `CHANGELOG.md` heading `## 2.0.0 (pending)`, internal Python names in user-facing changelog text, redundant `@pytest.mark.core` on `tests/test_artifact_meta_legacy.py`, abbreviated module citations, and omitted targeted pytest output / `--phase pre-transition --agent` in `V-05` | Dated live-corpus observation (`1,523` on 2026-11-21) as context only, cited exact `CHANGELOG.md` heading and wrote plain user-facing changelog prose, noted module-level `pytestmark = pytest.mark.core`, qualified symbol citations to `path::Symbol`, and added targeted pytest output and `aw ipd lint --phase pre-transition --agent` to `V-05` | PR-004, `steps/p-proofread.md` Section 11.1, `steps/r2-executability.md` |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes; changes `agent_workflows/artifact_meta.py::load_legacy_review` and `agent_workflows/meta_cli.py::check_meta` round-extraction behavior and SQLite `review_files.round_count` / `reviews` projections relied on by `aw show --history`, `aw check meta`, and metadata-v2 migration parity.
2. No; touches no private-data sanitizer, commit helper, worktree isolation, merge-to-main, or sandbox code.
3. No; cohesive (`5` E-items in `1` task group across `2` related metadata modules, `3` test files, and `CHANGELOG.md`).
4. Yes; `- Scope-Paths:` explicitly lists all `7` files (`agent_workflows/artifact_meta.py`, `agent_workflows/meta_cli.py`, `tests/test_artifact_meta_legacy.py`, `tests/test_show_history.py`, `tests/test_check_meta.py`, `CHANGELOG.md`, and this plan).
5. Yes; changing `load_legacy_review` without updating `tests/test_check_meta.py::test_drift_review_rounds` breaks the core test suite, and leaving `agent_workflows/meta_cli.py::_ROUND_HEADING_RE` unaligned causes false `meta.review-rounds-drift` errors in `aw check meta`.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261117-metastore-01-lz1igw-fix-load-legacy-review-round-parsing-to-match-anch.backlog.md`, spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (`4.1a K5a`, `4.6`, `4.9.1`), `agent_workflows/artifact_meta.py` (`load_legacy_review`, `_load_sources`, `history`, `review_rows`), `agent_workflows/meta_cli.py` (`_ROUND_HEADING_RE`, `check_meta`), `agent_workflows/review_findings.py` (`_ROUND_RE`, `_FENCE_RE`, `parse_review_text`), `agent_workflows/migrations/m0001_convert.py` (`_parse_review_file_raw`), `tests/test_artifact_meta_legacy.py`, `tests/test_show_history.py`, `tests/test_check_meta.py`, `CHANGELOG.md`, and a live scan of `.aw/records/reviews/` (`1,523` files: `4` with `## Round 1 escalation`, `29` sparse/high rounds, `3` reverse-ordered).
- Found critical missing coupling in `tests/test_check_meta.py::test_drift_review_rounds` (`PR-001`) and `agent_workflows/meta_cli.py::check_meta` (`PR-002`), plus stale live-corpus count (`1,516` -> `1,523`) and citation polish (`PR-004`). All fixed in place.

### Step R2

- Checked: `E-*`/`V-*` bijection (`5/5`: `E-01..E-05` <-> `V-01..V-05`, `- Highest E allocated: 05`), dependency chain (`E-01 -> E-02, E-03, E-04 -> E-05`), `- Scope-Paths:` completeness (`7` files), `- Item-Dependencies: none`, runtime reachability of `V-01..V-05`, and `Approval and execution gate`.
- Found incomplete execution contract in `Approval and execution gate` (`PR-003`) and missing targeted pytest output / `--phase pre-transition --agent` in `V-05` (`PR-004`). Fixed in place.

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). `load_legacy_review` and `check_meta` parse local repository Markdown in memory via `review_findings.parse_review_text` (stdlib regex line scan, no shell execution, no network calls, no secret handling, and no ReDoS risk).

### Step R4

- Checked: correctness and data integrity (`doc.rounds` preserves duplicate round headings for `check_meta` duplicate detection while `sorted(set(parsed_rounds))` deduplicates and orders `load_legacy_review` identically to `m0001_convert._parse_review_file_raw`; `parse_review_text` ignores YAML mirrors, fenced blocks, and unanchored headings), anti-regression (`PR-001` prevents guaranteed core-suite failure in `tests/test_check_meta.py::test_drift_review_rounds`; `PR-002` prevents false `meta.review-rounds-drift` errors in `aw check meta`), testing completeness, right-sizing (`5` focused E-items, `7` Scope-Paths), and `## Spec / documentation sync` (`4sd62s` `4.1a`, `4.6`, `4.9.1`, and `CHANGELOG.md`).

### Step S5

- Checked: `## Open questions` (`OQ-01` already `resolved`, `Blocking: no`). Recorded `D-1` in `### Decisions` for including `agent_workflows/meta_cli.py::check_meta` and `tests/test_check_meta.py::test_drift_review_rounds` inside `sz4h5i` (`Reversible: yes`). Zero blocking or human-owned questions remain.

### Pass 2

- Re-checked the complete revised plan after adding `E-04`/`V-04`, shifting `E-05`/`V-05`, updating `- Highest E allocated: 05`, and expanding `- Scope-Paths:` to `7` files.
- Verified full internal consistency across `Concern`, `Scope`, `Scope-Paths`, `Goal`, `E-01..E-05`, `V-01..V-05`, `F-01..F-04`, `Proposed changes`, Mermaid diagram, `Deferred / out of scope`, `Scope check`, `Required tests / validation`, `Spec / documentation sync`, `OQ-01`, and `Approval and execution gate`, with clean `aw ipd lint --phase review-finalize --agent` disposition.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | BLOCKER | UNDER-SCOPE | R1 / R4 / Core-suite regression in `test_check_meta.py` | tests/test_check_meta.py::test_drift_review_rounds:403-425; tests/test_check_meta.py:22; .aw/records/plans/pending/20261119-lz1igw-01-sz4h5i-fix-load-legacy-review-round-parsing-to-match-anchored-headi.ipd.md:7 | `tests/test_check_meta.py::test_drift_review_rounds` (marked `pytestmark = pytest.mark.core`) asserts `meta.review-rounds-drift` on a sparse `[1, 3]` review file specifically because `load_legacy_review` previously synthesized `[1, 2, 3]`. Landing `E-01` without updating `tests/test_check_meta.py` immediately breaks the core test suite (`rc == 0` instead of `1`), and `tests/test_check_meta.py` was absent from `- Scope-Paths:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `tests/test_check_meta.py` to `- Scope-Paths:` and added `E-04`/`V-04` updating `test_drift_review_rounds` to test genuine duplicate/logged-drift errors plus non-drift on sparse, unanchored, and fenced review files (`D-1`). Recommendation strength: very strong. |
| PR-002 | HIGH | UNDER-SCOPE | R1 / R4 / Divergent unanchored regex in `meta_cli.check_meta` | agent_workflows/meta_cli.py::_ROUND_HEADING_RE:628; agent_workflows/meta_cli.py::check_meta:1145-1172; agent_workflows/review_findings.py::parse_review_text:564-583 | `agent_workflows/meta_cli.py::check_meta` uses the same unanchored regex `r"^## Round (\d+)"` (ignoring code fences) to compare file rounds against `legacy_review_rounds` and `logged_review_rounds`. Once `E-01` switches `load_legacy_review` to `review_findings.parse_review_text`, `aw check meta` will disagree with cached rows and emit false `meta.review-rounds-drift` errors on review files with unanchored headings (such as the 4 real repo files containing `## Round 1 escalation`) or fenced `## Round` text. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `agent_workflows/meta_cli.py` to `- Scope-Paths:` and added `E-04`/`V-04` replacing `_ROUND_HEADING_RE.findall` with `[r.number for r in review_findings.parse_review_text(rf_text).rounds]` (which preserves duplicates for `len(file_rounds) != len(set(file_rounds))`) (`D-1`). Recommendation strength: very strong. |
| PR-003 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261119-lz1igw-01-sz4h5i-fix-load-legacy-review-round-parsing-to-match-anchored-headi.ipd.md:163-168; .aw/system/workflows/plan-review/steps/r2-executability.md:57-60; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | `Approval and execution gate` used ambiguous finalize ownership ("through `aw ipd finalize sz4h5i` (or runner self-finalize)") and omitted the resolved-open-questions precondition, `--scope-reason`/`--scope-ack` scope-fence variance rule, shared-checkout safety rule, explicit hand-`git mv` prohibition, and post-finalization backlog `lz1igw` closure note. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` with all required execution-contract clauses, explicit conditional runner/executor `aw ipd finalize sz4h5i` ownership, hand-`git mv` prohibition, and separate post-finalization backlog `lz1igw` closure. Recommendation strength: very strong. |
| PR-004 | LOW | IN-SCOPE | Proofreading / R1 / R2 / Citations, counts, and V-05 alignment | .aw/records/plans/pending/20261119-lz1igw-01-sz4h5i-fix-load-legacy-review-round-parsing-to-match-anchored-headi.ipd.md:46,61,81-83,116,128,159; tests/test_artifact_meta_legacy.py:16; CHANGELOG.md:7 | `F-01`/`F-02`/`Scope check` cited a drifted live count (`1,516` vs `1,523` on 2026-11-21); `E-04` cited truncated `CHANGELOG.md` heading `## 2.0.0 (pending)` and internal Python names in user-facing prose; `E-02` requested redundant `@pytest.mark.core` where module-level `pytestmark` already applies; `V-04` omitted targeted pytest output and `--phase pre-transition --agent` on `aw ipd lint`; and several symbol citations were abbreviated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Dated live-corpus context (`1,523` on 2026-11-21), qualified citations to `path::Symbol`, cited the exact `CHANGELOG.md` heading with user-facing prose, noted module-level `pytestmark`, and aligned `E-05`/`V-05` with targeted pytest output and `aw ipd lint --phase pre-transition --agent`. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should `agent_workflows/meta_cli.py::check_meta` and `tests/test_check_meta.py::test_drift_review_rounds` be updated inside `sz4h5i` rather than deferred to a separate follow-up? | Include both in `sz4h5i` as `E-04`/`V-04` and add both paths to `- Scope-Paths:`. | Defer `meta_cli.py` and `test_check_meta.py` to a separate plan (rejected: `tests/test_check_meta.py::test_drift_review_rounds` is `@pytest.mark.core` and breaks immediately when `E-01` lands, making bare `python3 -m pytest` fail until updated, and leaving `meta_cli.py` on `_ROUND_HEADING_RE` creates immediate disagreement with `load_legacy_review`). | `tests/test_check_meta.py::test_drift_review_rounds:403-425`, `tests/test_check_meta.py:22`, `agent_workflows/meta_cli.py::_ROUND_HEADING_RE:628`, `agent_workflows/meta_cli.py::check_meta:1145-1172` | yes |
