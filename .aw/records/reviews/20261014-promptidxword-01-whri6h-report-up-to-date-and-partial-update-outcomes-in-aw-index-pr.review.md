# Review findings: plan whri6h

- Subject-Id: whri6h
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review lane. The plan was already committed and unchanged at `e4e02ba0e`, so no pre-review snapshot was needed. `aw ipd lint --phase author` reported conforming before and after the revisions.

Claims I verified at HEAD:
- `prompts_index.run_index` computes `json_changed`/`md_changed`, then returns early through `_core.emit_index_write_result` for `--agent`/`--json`. Its human block runs `print(f"wrote {INDEX_JSON} ({len(entries)} prompts)")` and then `print(f"wrote {INDEX_MD}")` unconditionally.
- The four-state blocks in `plans_index.run_index` and `research_index.run_index` match the plan's code exactly.
- `ROLE_COLOR_256` maps `wrote`, `up to date`, and `updated` to 46.
- Subprocess probe via `run_cli(["index", verb])` on the `_setup_fixture_for_verb` fixture. Four runs each: first, unchanged, INDEX.md-only edit, INDEX.json-only edit. Prompts printed the legacy two lines all four times. Plans and research printed `wrote`, `up to date`, `updated ... INDEX.md`, `updated ... INDEX.json`, so extending the subprocess test to those two verbs needs no code change.
- In-process probe on the `PromptsIndexTests.setUp` fixture: `scan_prompts` returns 3 entries and no drift, so `(3 prompts)` is correct.
- The only other caller, `status_set._auto_index_types`, passes `quiet=True`.
- `CHANGELOG.md` has no `[Unreleased]`/`### Fixed`. Fixes go in as `- Fixed:` bullets under `## 2.0.0 (pending)`.
- `aw check all --agent` exits 1 at HEAD with 27 errors that are repository-wide and unrelated to this plan.
- `aw ipd lint --phase pre-transition` initially reported `check.ipd-uncarried-obligation` on the Deferred row "None."

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Evidence feasibility | `aw check all --agent`: `exit 1`, `{"error":27,...}` at HEAD | E-04/V-04 required `aw check all` to exit 0, which is impossible for reasons outside this plan. The executor would have had to fail the plan or misreport. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with `aw ipd lint --phase pre-transition` and `aw check release-gates`, which exited 0 at review. The reason is stated in E-04. |
| PR-002 | HIGH | UNDER-SCOPE | G. Lifecycle gate | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation: ... deferred row 1` | The "- None." Deferred row has no carrier, so the plan could not finalize. | all Low | FIXED | Replaced it with a real out-of-scope item (factor the triplicated four-state block into a shared helper) carrying a reasoned `Carrier-Declined`. Lint is clean. |
| PR-003 | MEDIUM | IN-SCOPE | G. Evidence anchors | `CHANGELOG.md` headings `## 2.0.0 (pending)` with `- Fixed:` bullets | E-04, Proposed changes, and V-04 named `## [Unreleased]` / `### Fixed`, which do not exist. | all Low | FIXED | Each now targets a `- Fixed:` bullet under `## 2.0.0 (pending)`. |
| PR-004 | MEDIUM | UNDER-SCOPE | G. Execution contract | old gate: one sentence, "finalize the plan via `aw ipd finalize whri6h`" | The gate told the executor to finalize unconditionally. It had no approval step, scope fence, honesty rule, commit discipline, or never-push/never-tag rule. The plan file was missing from Scope-Paths. | all Low | FIXED | Rewrote the gate in the repo's standard form, with finalize owned by the runner and done by the executor only when running by hand. Added the plan path to Scope-Paths. |
| PR-005 | MEDIUM | IN-SCOPE | E. Verification strength | old V-01 (diff only), V-02/V-03 (bare pass) | No V-item showed the CLI behaving correctly, the new tests had no proof they could fail, and `quiet=True` was not shown to still write. | all Low | FIXED | V-01 adds a four-run CLI observation. E-02/V-02 add a non-vacuity run using an in-process patch only. E-02 (e) asserts the quiet write still happens. V-02/V-03 use `-o addopts="" -v`. |
| PR-006 | LOW | IN-SCOPE | G. Precision | old E-01 / Proposed code re-imported `select_output`; drift loop and lifecycle-resolver note unmentioned; E-02 fixture unspecified; E-03 docstring stale; OQ-01 point (3) cited `cli._run_noun_verb` looping a tuple not found there | Small gaps that would leave the executor guessing. | all Low | FIXED | E-01 reuses the existing import, preserves the drift loop, and adds a pointer comment. E-02 names the fixture and the Namespace. E-03 refreshes the docstring and adds named expectation dicts. Dropped the unverifiable OQ-01 claim. The spec path and criteria are now cited exactly. |

`aw ipd lint --phase review-finalize` reported conforming after the revisions.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which repo-wide gate replaces `aw check all`? | `aw ipd lint --phase pre-transition` + `aw check release-gates` | Keep `check all` (unsatisfiable); drop gates entirely | Measured exits at review: `check all` 1, `release-gates` 0 | yes |
| D-2 | Fold a shared four-state helper into this plan? | No, declined with reason | Extract into `artifact_core` now | `vcqobe` scope; the other two verbs are already correct and pinned | yes |
| D-3 | Extend the subprocess partial-update test to plans and research too? | Yes | Prompts only | Probe showed both already pass, so the extension adds coverage at no code risk | yes |
