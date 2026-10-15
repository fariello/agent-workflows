# Review: Restore behavioral coverage of approved-orchestrator end-to-end derivation and legacy manifest kind fallback

- Subject-Id: 33wan5
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `eaafddbcb`, clean tree, target plan committed unchanged (snapshot skipped).
`aw ipd lint --phase author` conforming before revisions; `--phase review-finalize` conforming after.

Verified TRUE: `runner_shared.plan_kind_from_file` and `runner_shared.resolve_manifest_kind` exist and are
re-exported by both hosts; `rg "resolve_manifest_kind|plan_kind_from_file" tests/` is empty;
`runner_shared.initialize_run_core` loads `args.manifest` through `load_json` + `validate_manifest` and calls
`resolve_manifest_kind(plan, p_path)` at the queue build and `resolve_manifest_kind(item_info, probe_path)`
in the legality preflight; `SCHEMA_VERSION = 1`; the three comment sites exist (banner "THE FAILURE MODE
HERE IS SILENT AND TYPE-SHAPED", `PlanRecord` docstring "DO NOT DROP `kind`", agy "`_plan_kind` HAD TWO
CALLERS"). A one-off probe (deleted afterwards) drove each host's real `initialize_run` with a kind-less
hand-written manifest and `prepare_only=True`: both hosts produced `orchestrate`/`orchestrator`; under
`mock.patch.object(runner_shared, "resolve_manifest_kind", lambda e, p: e.get("kind"))` both produced
`execute`/`None`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | D. Anti-regression (vacuous control) | Plan E-04 original text; `runner_shared.action_for` | E-04's control asserted only `action_for(None, "approved") == "execute"`, a constant fact independent of the fallback, so it could not show the E-02/E-03 assertions depend on `resolve_manifest_kind`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now reruns the E-03 queue-build helper under a `mock.patch.object` pass-through resolver and asserts `execute`/`None` on both hosts; feasibility demonstrated by the review probe. Depends-on moved to E-03. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing (unsatisfiable demand) | `agent_workflows/runner_shared.py` banner wraps "no" / "live guard currently asserts this derivation" across two lines; many unrelated "no live guard currently asserts" comments exist in both files | E-05's expected outcome (an `rg` one-line grep returning no matches "for these three sites") cannot be read off the grep: the banner instance never matches a single-line grep, and unrelated sites legitimately remain. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now states the per-site property, warns about the wrap, and requires untouched unrelated sites; V-05 checks exactly the three named sites in the diff. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Executability (execution contract) | Plan's original Approval gate paragraph | The gate lacked a scope fence declaration, the paste-actual-runner-output rule, `--no-verify`/staged-set guidance, revert of the V-02 scratch edit before commit, and the conditional runner/executor lifecycle ownership (it unconditionally told the executor to finalize). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with EXECUTION CONTRACT and POST-GATE LIFECYCLE MOVE paragraphs; plan file added to Scope-Paths. |
| PR-004 | LOW | IN-SCOPE | E. Testing (fixture validity) | `runner_shared.validate_manifest` requires `sets` with `order` and a known `schema_version` | E-03 did not say the manifest needs a `sets` entry, nor how to build the `Namespace`; an executor could produce a manifest `validate_manifest` refuses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 names `runner_shared.SCHEMA_VERSION`, the `sets` entry, the `Namespace` precedent in `TheActionDecisionIsSHAREDCode`, and an assertion that the JSON omits `kind`. |
| PR-005 | LOW | IN-SCOPE | G. Live-artifact criteria convention | V-01 used `-k EndToEnd` and subTest ids as the bar; E-01/E-02 named no classes | V-items barred on test-organization artifacts (a `-k` filter that matches nothing if the class is named differently). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Classes named in E-01/E-02 as pointers; V-01..V-04 now demand the pinned behavior with zero failures. V-02's scratch-run demand narrowed to the kind-less-orchestrator test (the explicit-kind and missing-file tests correctly keep passing). |
| PR-006 | LOW | IN-SCOPE | Plan-review 3.1 (Owner) | Plan OQ-01 `- Owner: none` | A resolved question with `Owner: none`; the resolution is the plan author's reading of the backlog item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Make the non-vacuity control permanent (mock) or keep only the one-off scratch edit? | Both: a permanent mock-patched test plus the one-off scratch run in V-02. | Scratch-only: rejected, leaves no durable guard against a vacuous fallback assertion. Mock-only: rejected, the scratch edit additionally proves the E-02 direct-call tests bite. | Review probe output at `eaafddbcb`; `runner_shared.initialize_run_core` calls `resolve_manifest_kind` by module global | yes |
| D-2 | Restore the deleted structural pins (OQ-01)? | No (author's resolution confirmed). | Restore them: rejected by P16 and the backlog item text. | Backlog `8ww1zo` body; AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE" | yes |
