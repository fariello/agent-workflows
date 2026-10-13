# Review findings: plan k81fqx

- Subject-Id: k81fqx
- Subject-Type: ipd
- Reviewed-At: 2026-10-13
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `559173a5c`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `- Kind: child`. `aw ipd lint --phase author` and `--phase review-finalize` reported `clean`.

Verified at review: the faulty line `target = dependency_target_id6(edge) or dep` sits in `runner_shared.dependency_status_detailed` after `edge_satisfied`, under the comment "Uses the parsed edge's target id6, not the raw token" (F-03 confirmed); `dependency_target_id6(token: str)` re-parses its argument and returns `None` for an `ItemDependency`; the two other callers pass `str(dep)`; `_findings_block_reason` delegates to `review_findings.subject_gating_blocks`, which matches `doc.subject_id` by exact equality. A temp-repo probe reproduced F-02 for the `executed:` form both out of queue and in queue (`(True, [], {})` despite a HIGH OPEN finding), and with `edge.id6` substituted (monkeypatched) all three execute cases block with reason `dep001: review finding PR-001 is high/open and unresolved` while a `review` item stays satisfied. Corpus re-measured: 10 gating subjects (same ids as F-05), 0 pending plans with an edge to one. All five existing consumer test files named under Required tests exist; the new test module does not yet exist.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E (test design / evidence feasibility) | Plan E-02 Expected outcome "cases (a) (b) (c) FAIL on the pre-fix code"; V-02 same; `runner_shared.dependency_status_detailed` `or dep` fallback; review probe: pre-fix bare `dep001` -> `(False, ['dep001'], {...PR-001 high/open...})` | For a bare-id6 dependency the raw-token fallback already IS the id6, so case (b) blocks before the fix. V-02 demanded a failure that cannot happen, which would force the executor either to refuse V-02 or to bend the test until it fails. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Case (b) is now a characterization case expected to pass before and after. E-02/V-02 and Required tests require (a) and (c) to fail without E-01, and (b) to pass. Added F-08. |
| PR-002 | MEDIUM | UNDER-SCOPE | E (vacuous test risk) | `review_findings.parse_review_text` attributes table rows only under `### Findings` (`H_FINDINGS`); review probe: a record without the heading -> `subject_gating_blocks(repo,'dep001') == ()` and every case satisfied | E-02 described the fixture only as "a record carrying one finding". A natural heading-less fixture parses to zero findings, so the blocked cases fail for the wrong reason before the fix and the satisfied cases pass vacuously. The revert proof would then be uninterpretable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires the `### Findings` heading (preferably via `review_findings.render_review`/`write_review`) and a sanity assertion that `subject_gating_blocks` is non-empty in the blocked cases. |
| PR-003 | MEDIUM | UNDER-SCOPE | G (lifecycle gate) / `check.ipd-uncarried-obligation` | `aw check all --agent` listed `check.ipd-uncarried-obligation` (severity error) for this plan | The three Deferred rows had no `Carrier`/`Carrier-Declined`, which `aw ipd lint --phase pre-transition` would refuse at the terminal transition. The gate also said no `- Readiness:` is written, which goes stale once a review records it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each row carries `- Carrier-Declined:` with its reason. The gate sentence now states human approval is required and that there are no open questions. E-03's count is re-derived at execution (context, not bar). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Keep case (b) or drop it once it cannot demonstrate the fix? | Keep it as a characterization case that must pass before and after. | Drop it; keep demanding it fail. | The bare form is a legal token (`parse_dependency_token` normalizes a bare id6 for hand-written manifests), so pinning that E-01 does not regress it has value; demanding it fail is unsatisfiable (review probe). | yes |
