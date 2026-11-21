# Review findings: ipd rowsi5

- Subject-Id: rowsi5
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `0a8d832e1892ff128250c6458c7add6d5b87e123` in an isolated runner review-sweep lane worktree. The target plan `.aw/records/plans/pending/20261119-5uqo2g-01-rowsi5-hoist-generic-test-git-identity-tokens-into-leak-sanitizer.ipd.md` was committed and clean at turn start, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`exit: 0`, `error: 0`, `warning: 0`, `info: 2` on the boilerplate `IPD-C802` em-dashes). Inspection against backlog `5uqo2g`, `agent_workflows/leak_sanitizer.py`, `agent_workflows/artifact_meta.py`, `tests/test_local_leaks.py`, `tests/test_artifact_meta_write.py`, `tests/test_leak_sanitizer.py`, and `tests/test_generators_writing_standard_pointer.py` uncovered a critical factual mismatch (`PR-001`: `_writer_ruleset` no longer has an `in_lane` guard and pops `reason == "sibling checkout dir name"` unconditionally), an incomplete execution gate (`PR-002`), test-fixture vacuity risks (`PR-003`), and `- Scope-Paths:` / boilerplate hygiene issues (`PR-004`). All four findings had `Low` Remediation Risk and were fixed in place. Pass 2 re-checked every section after the `- Scope-Paths:` and `E-02`/`V-02` edits and confirmed clean `aw ipd lint --phase review-finalize --agent`.

### Proofreading

Checked `.aw/records/plans/pending/20261119-5uqo2g-01-rowsi5-hoist-generic-test-git-identity-tokens-into-leak-sanitizer.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Front matter | `- Status: to-review`, missing `- Readiness:` / `- Review-Depth:`, `- Scope-Paths:` included the plan's own path, `- Scope:` named runner-lane sibling filter | Transitioned `- Status: reviewed` via `aw ipd set`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard`, narrowed `- Scope-Paths:` to the 4 code/test files, and updated `- Scope:` to reference the unconditional `reason == "sibling checkout dir name"` filter | PR-001, PR-004, Step S7 |
| Workflow history | `to-review` and `draft` lines only | Prepended `aw set` `reviewed` and `/plan-review` lines citing `APPROVE WITH REVISIONS APPLIED`, `PR-001..PR-004`, and this review record | Step S7 newest-first history contract |
| `E-02`, `Findings` F-04, `Behavior decisions`, `Proposed changes` #2, Mermaid flowchart, `V-02` | Claimed `_writer_ruleset` gated sibling-dir filtering on `in_lane and reason == "sibling checkout dir name"` and demanded `in_lane` remain in `git diff` | Aligned all six locations with actual `agent_workflows/artifact_meta.py::_writer_ruleset` (`if reason == "sibling checkout dir name":` unconditionally for both `.aw/worktrees/` lanes and normal workspaces) and explicitly forbade re-introducing `in_lane` | PR-001, Technical writing standard Requirement 12(d) |
| `E-03`, `E-04` | `E-03` committed only `"Test"` and `"test@example.com"` across four identity cases; `E-04` did not specify anchoring `records_root` inside the `tmp_path` repo or `fields["title"]` | Required `E-03` to commit each case's own configured identity tokens (including mixed-case `"TEST@EXAMPLE.INVALID"`) and `E-04` to set `records_root = repo / ".aw" / "records"` and pass `fields["title"]` and `message` | PR-003 |
| Checklist trailing boilerplate and `Scope check` | Retained `Add further leaves as - [ ] E-NEW` line and referenced plan file in `Scope check` | Removed `E-NEW` template line and aligned `Scope check` with the 4 work `- Scope-Paths:` | PR-004 |
| `Approval and execution gate` | Unconditionally instructed finalizing to `executed/` and omitted resolved-OQ, `--scope-reason`/`--scope-ack`, never-push, paste-actual-output, no-hand-`git mv`, and conditional runner/executor finalize ownership clauses | Rewrote with all required execution-contract clauses | PR-002, Step R2, Step S7 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |

### Step T

1. Yes: changes the shared advisory leak-derivation exemption set (`agent_workflows/leak_sanitizer.py::_GENERIC_DERIVED_TOKENS`) consumed by `derive_warn_tokens`, `build_ruleset(..., include_warn=True)`, `artifact_meta._writer_ruleset`, `artifact_adopt`, `install_history`, and `m0001_verify`.
2. Yes: directly edits `agent_workflows/leak_sanitizer.py` (an explicit private-data/leak guard module in Check T question 2) and `agent_workflows/artifact_meta.py::_writer_ruleset`.
3. No: 4 `E-*` items in 2 task groups across 4 cohesive files.
4. Yes: `- Scope-Paths:` explicitly lists all 4 affected code and test files.
5. Yes: over-broadening `_GENERIC_DERIVED_TOKENS` could suppress real personal leak warnings, and executing the stale `in_lane` wording in `E-02`/`V-02` would regress normal-workspace sibling directory filtering (e.g. `../uri`).

`AW-TIER: standard`

### Step R1

- Checked: `.aw/records/backlog/graduated/20261117-5uqo2g-01-5uqo2g-generic-test-git-identity-leak-tokens.backlog.md`, `agent_workflows/leak_sanitizer.py` (`_FAIL_PATTERNS:72`, `_GENERIC_DERIVED_TOKENS:135`, `derive_warn_tokens:472`, `build_ruleset:550`), `agent_workflows/artifact_meta.py` (`_check_leak_sanitizer:850`, `_GENERIC_FIXTURE_GIT_TOKENS:939`, `_writer_ruleset:952-976`, `validate_new_events:979`, `create:7560`), `tests/test_local_leaks.py` (`AutoDeriveTests:576`), `tests/test_leak_sanitizer.py` (`SelfCleanTests:69`, `RuleTierTests:548`), `tests/test_artifact_meta_write.py`, `tests/test_generators_writing_standard_pointer.py`, and `tests/test_core_module_coverage.py`.
- Found `PR-001` (`_writer_ruleset` has no `in_lane` guard at HEAD; it removes `sibling checkout dir name` unconditionally).

### Step R2

- Checked: `E-*`/`V-*` bijection (`4/4`: `E-01..E-04` <-> `V-01..V-04`, `- Highest E allocated: 04`), dependency chain (`E-01 -> E-02`, `E-01 -> E-03`, `E-01, E-02 -> E-04`), `- Scope-Paths:` accuracy, `- Item-Dependencies: none`, `- From-Backlog: 5uqo2g`, `- Blocks-Release: next`, carrier obligations (`Carrier-Declined` on Deferred row), runtime reachability of `V-01..V-04`, and `Approval and execution gate`.
- Found `PR-002` (incomplete execution contract and unconditional finalize wording) and `PR-004` (self-referential plan file in `- Scope-Paths:` and leftover `E-NEW` template line). Fixed both in place.

### Step R3

- Checked: security and privacy full form (`steps/r3-security.md`). Audited all 18 synthetic test-fixture tokens proposed for `_GENERIC_DERIVED_TOKENS` (`"test"`, `"tester"`, `"test user"`, `"test runner"`, `"test agent"`, `"test committer"`, `"test author"`, and RFC 2606 / synthetic `@example.com`, `@example.invalid`, `@test.com`, `@test.local` addresses): none is a real personal identifier, real domain, or secret; none matches `_FAIL_PATTERNS` (preserving `SelfCleanTests::test_engine_source_is_self_clean`); `_FAIL_PATTERNS` remain completely untouched; removing `_GENERIC_FIXTURE_GIT_TOKENS` from `artifact_meta.py` eliminates a duplicated allowlist; and both `E-03` and `E-04` pair suppression checks with non-generic probe controls so a broken detector cannot pass vacuously.

### Step R4

- Checked: correctness and data integrity (single source of truth in `leak_sanitizer._GENERIC_DERIVED_TOKENS`, preserving `_writer_ruleset` sibling-directory filtering without re-introducing `in_lane`), anti-regression and P16 behavioral testing (`E-03` commits each case's own tokens including mixed-case folding; `E-04` anchors `records_root` inside the `tmp_path` git repo so `_writer_ruleset` reads local fixture config), right-sizing (4 focused E-items across 4 files), and `## Spec / documentation sync` (`N/A` accurately justified).
- Found `PR-003` (potential vacuous coverage in `E-03` for `"Tester"`, `"Test User"`, and `"test@example.invalid"`, and unanchored `records_root` in `E-04`). Fixed in place.

### Step S5

- Checked: `## Open questions` (`None open.`). Confirmed backlog `5uqo2g` and repository evidence resolve hoisting into `_GENERIC_DERIVED_TOKENS` cleanly without altering `tests/support.py::init_repo`. Recorded autonomous review decisions `D-1`..`D-2` in `### Decisions` (both `Reversible: yes`). Zero blocking or human-owned open questions remain; all findings `PR-001`..`PR-004` are `FIXED` in place.

### Pass 2

- Re-checked front matter, `## Workflow history`, `## Goal`, `E-01..E-04`, `Project conventions discovered`, `Findings`, `Behavior decisions`, `Proposed changes`, Mermaid flowchart, `Deferred / out of scope`, `Scope check`, `Required tests / validation`, `Spec / documentation sync`, `Open questions`, `V-01..V-04`, and `Approval and execution gate` after all revisions.
- Confirmed zero remaining stale `in_lane` references anywhere in the plan, `4/4` bijection, clean `- Scope-Paths:`, and clean `aw ipd lint --phase review-finalize --agent` disposition.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PR-001 | BLOCKER | IN-SCOPE | R1 / R4 / Factual contradiction | agent_workflows/artifact_meta.py:952 `_writer_ruleset`; .aw/records/plans/pending/20261119-5uqo2g-01-rowsi5-hoist-generic-test-git-identity-tokens-into-leak-sanitizer.ipd.md:6, :43, :83, :97, :137 | Six sections claimed `_writer_ruleset` gates sibling-dir filtering on `in_lane and reason == "sibling checkout dir name"`, and `V-02` required `in_lane` to remain in the diff. At HEAD, `in_lane` was intentionally removed so sibling dir names are popped unconditionally (both in `.aw/worktrees/` lanes and normal workspaces); executing as written would fail `V-02` or regress normal-workspace sibling filtering. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `Scope`, `E-02`, `Findings` F-04, `Behavior decisions`, `Proposed changes` #2, Mermaid diagram, and `V-02` to preserve the unconditional `if reason == "sibling checkout dir name":` filter and explicitly forbid re-introducing `in_lane`. Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261119-5uqo2g-01-rowsi5-hoist-generic-test-git-identity-tokens-into-leak-sanitizer.ipd.md:149 | `Approval and execution gate` unconditionally instructed finalizing to `executed/` and omitted resolved-OQ precondition, `--scope-reason`/`--scope-ack`, never-push, paste-actual-runner-output honesty rule, hand-`git mv` prohibition, and conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` with every required execution-contract clause including conditional runner (`AW_EXECUTION_ROLE=worker`) vs standalone executor finalize ownership. Recommendation strength: very strong. |
| PR-003 | MEDIUM | IN-SCOPE | R3 / R4 / Non-vacuous test coverage | .aw/records/plans/pending/20261119-5uqo2g-01-rowsi5-hoist-generic-test-git-identity-tokens-into-leak-sanitizer.ipd.md:50, :55; agent_workflows/artifact_meta.py:897 `_resolve_repo_root` | `E-03` committed only `"Test"` and `"test@example.com"` while testing four generic identities (leaving `"Tester"`, `"Test User"`, and `"test@example.invalid"` unexercised by `ll.run`), and `E-04` did not specify anchoring `records_root = repo / ".aw" / "records"` or `fields["title"]`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-03` to commit each case's own configured identity tokens (including mixed-case `"TEST@EXAMPLE.INVALID"`) and `E-04` to anchor `records_root = repo / ".aw" / "records"` and pass `fields["title"]` and `message`. Recommendation strength: strong. |
| PR-004 | MEDIUM | IN-SCOPE | R2 / Proofreading / Hygiene | .aw/records/plans/pending/20261119-5uqo2g-01-rowsi5-hoist-generic-test-git-identity-tokens-into-leak-sanitizer.ipd.md:7, :60 | `- Scope-Paths:` redundantly listed the plan's own path and line 60 retained the `Add further leaves as - [ ] E-NEW` template boilerplate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed the plan path from `- Scope-Paths:` (keeping the 4 work paths) and deleted the `E-NEW` template line. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D-1 | How should `E-02` and `V-02` treat the `sibling checkout dir name` filter in `agent_workflows/artifact_meta.py::_writer_ruleset`? | Preserve the unconditional `if reason == "sibling checkout dir name":` filter at HEAD and explicitly forbid re-introducing `in_lane`. | Re-introduce `in_lane` to match the stale plan text (would regress normal-workspace sibling repos like `../uri`). | `agent_workflows/artifact_meta.py:952-976` and git history removing `in_lane` | yes |
| D-2 | Should `E-03` commit each case's own generic identity tokens (with mixed case) and `E-04` anchor `records_root = repo / ".aw" / "records"`? | Yes: ensures `local_leaks.run` actually scans every tested generic identity token and `_writer_ruleset` reads the fixture repository's local `git config`. | Commit only `"Test"` and `"test@example.com"` (leaves other cases vacuous under `ll.run`). | `agent_workflows/leak_sanitizer.py:481-505`; `agent_workflows/artifact_meta.py:897-911`; `GUIDING_PRINCIPLES.md` P16 | yes |
