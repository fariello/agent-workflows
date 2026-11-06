# Review findings: plan 9en4fy

- Subject-Id: 9en4fy
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Interactive review at HEAD `30b49d36c`, in the shared checkout. The plan was authored in the same session as its code, and the maintainer approved it from the instruction "Let's address these. Use the repos conventions."; `aw ipd begin` then refused with `IPD-M113` because no review had run, so this review was run rather than writing the field by hand. `aw ipd lint --phase author` reported only `IPD-M113` before the edits, and `--phase review-finalize` reported only `IPD-M113` after them. Probes used throwaway repositories and clones of the target repository outside this checkout.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-01 Expected outcome | Conforming at pre-transition only | Also conforming at pre-execution; annotated draft fails on its leading token | PR-001. |
| E-09 | Removes the citation from the message and scaffold | Also regenerates the shipped child template from `build_skeleton` | PR-002. |
| V-01 | `AnnotatedLegacyHeaderTests` only | Adds `AnnotatedApprovedPassesPreExecutionTests` | PR-001. |
| V-09 | Spec diff and core gate | Adds `tests/test_ipd_templates.py` parity | PR-002. |
| Scope-Paths | No template path | Adds `.aw/system/workflows/assess/templates/ipd.md` | PR-002. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. It amends spec `ipd-structure-and-linting` Section 13.2a, adds advisory code `IPD-L002`, adds a `- Prior-Status:` line that finalize writes, and changes the migrate-layout commit subject.
2. Yes. It changes finalize's scope audit (which paths need a `--scope-reason`) and the post-commit index gate.
3. Yes. 9 E-items in 3 task groups across `ipd_lint`, `ipd_lifecycle`, `status_set`, `ipd_authoring` and `cli`.
4. Yes, file by file.
5. Moderately. A too-wide rename exemption or a too-wide index exemption would let real out-of-scope work or a stale manifest pass finalize silently.

AW-TIER: standard

### Step R1

- Checked: `ipd_lint._apply_legacy_format`, `ipd_lint._is_legacy_format_diag`, `ipd_lint.check_checkpoint`, `ipd_schema.validate_metadata`, `ipd_schema.checkpoint_allows_status`, `ipd_lifecycle._STATUS_APPROVED_RE`, `ipd_lifecycle.derive_baseline`, `ipd_lifecycle.finalize_precheck`, `ipd_lifecycle._refresh_plans_index_fail_loud`, `ipd_lifecycle._finalize_transaction`, `ipd_lifecycle._complete_after_commit`, `ipd_lifecycle.run_finalize`, `status_set.apply_status_change`, `status_set._STATUS_RE`, `ipd_authoring.insert_id_line`, `plans_index.scan_plans`, `plans_index.check_drift`, `cli._report_and_commit_migration`, `layout_migration.MigrationManager.summarize`, `config.plan_predates_cutover`, `config.resolve_cutover_date`.
- F-1's timing claim was checked in the target repository: `git log -- .aw/config/project.json` names only the installer-sync commit, committed after the finalize commit.
- F-5's count was re-measured: `git diff -M --find-renames=100% --name-status <approval> <migration>` in the target repository gives 688 `R100` (465 from `.agents/`, 223 from `workflow-artifacts/`).
- F-8 was checked: `git show --stat` of the re-run migration commit changes only `.aw/config/config.json`.

### Step R2

- Checked: the E/V bijection (9/9), `Item-Dependencies: executed:18kg7o` (it is in `executed/`), the scope fence, and the reachability of each runtime demand.
- Reachability: every V demands a test result or lint output; the finalize demonstrations are driven by `cli.main(["ipd","finalize",...])` in the named test classes.
- PR-001: E-01 re-judged the checkpoint rule on the leading token but left the original `IPD-S404` on the raw value, so an annotated `approved` plan still failed `pre-execution` and `aw ipd begin` refused. Measured in a scratch repo: `IPD-S404 status 'approved (2026-09-25; executing)' is incompatible with checkpoint 'pre-execution'`.
- PR-002: the scaffold edit made `tests/test_ipd_templates.py::TemplateParityTests::test_child_template_matches_generator` fail ("child template drifted from build_skeleton; regenerate it"); the template was outside Scope-Paths.

### Step R3

- Checked: the two exemptions, because each widens what finalize accepts.
- The rename exemption is direction-bound and similarity-bound. Measured: a pure rename INTO `.agents/` (`src/b.py` -> `.agents/b.py`) and a pure rename from a non-legacy root into `.aw/` (`src/b.py` -> `.aw/x/b.py`) both still demand a `--scope-reason`; a rename from `.agents/` into `.aw/` whose content changed still demands one (`test_a_renamed_file_with_changed_content_still_needs_a_reason`).
- Accepted residual: a pure `git mv` from `.agents/` into `.aw/` done by hand inside the plan's window is excused even when it was not a migration. Recorded as D-1.
- The index exemption covers only the three per-plan rules on a different file; stale or missing manifests and dangling citations still raise, which `tests/test_ipd_lifecycle_cli.py` `test_fail_loud_arm_refuses_on_genuine_non_convergence` (a `name-metadata-mismatch` on the finalized plan itself) still proves.
- No secret or path is written; `- Prior-Status:` copies text already in the plan.

### Step R4

- A. Correctness: `status_set.apply_status_change` replaces exactly one annotated line, only when no bare-token line matched, only for plans, only above the first H2, only when the leading token is a recognized status.
- C. Operability: the new behavior reuses `plans.normalize_status`, the existing `IPD-FINALIZE` warning channel, and the existing scope-audit evidence dict.
- D. Invariants: an unrecognized annotated status still refuses (`IPD-M104`); an annotated non-ready status still fails pre-execution (`IPD-S404`); a post-cutover plan is untouched (existing `test_post_cutover_same_text_still_refused`).
- E. Testing: each E has a behavioral test driving real git repositories and the CLI.
- Spec sync: Section 13.2a amended and noted.

### Step S5

- Checked: OQ-01 (resolved from repository evidence: the migration commit carries no marker; demonstrated by the direction-bound probes in Step R3).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R2 executability | `agent_workflows/ipd_lint.py::_is_legacy_annotation_diag`; scratch repo `aw ipd begin` output | The raw-value `IPD-S404` survived the reduced check, so an annotated approved plan could not pass pre-execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The raw `IPD-S404` is dropped when the leading token differs; the leading token is re-judged. E-01 and V-01 updated; test added. |
| PR-002 | MEDIUM | UNDER-SCOPE | R2 scope fence | `tests/test_ipd_templates.py::TemplateParityTests.test_child_template_matches_generator` | The shipped child template is generated from `build_skeleton` and was not regenerated or declared. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Template regenerated; path added to Scope-Paths; E-09 and V-09 updated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Excuse every pure legacy-root -> `.aw/` rename, or only renames inside an `aw migrate-layout` commit? | Every pure rename of that shape | Marker-based detection (no marker exists in a target repo); excusing all renames (too wide) | the target repository's migration commit was hand-titled; Step R3 probes | yes |
