# Review findings: plan wix4xe

- Subject-Id: wix4xe
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032734Z-4093657` at HEAD `8bb406f45`. The plan was
committed and byte-identical to the sealed lane input (rev-10); no snapshot needed. `- Kind: child`, so `IPD-S407`/
`IPD-S408` do not apply. `aw ipd lint --phase author` clean before review. F-01..F-05 re-reproduced by driving the
code: one `skill-selection.md:27: [aw-command] 'aw router'` finding, `TypeError` on `json.dumps`, `[]` for an absent
dir. `t9lcdu` is `approved`, still in `pending/`; `usggph` is open.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E testing / falsifiability | `release_readiness.build_report`; measured bare tmp repo -> `NO-GO ['changelog_versioning', 'residual_risk']` | E-06(f)/V-05 asserted only `NO-GO` with `docs_checks` in failing gates over a bare tmp repo; the "clean does not list docs_checks" half also passes against the unwired gate, and NO-GO alone is vacuous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Contrast pair over a fixture satisfying all other gates: clean -> `GO []`, dirty -> `failing_gates() == ["docs_checks"]` (measured `GO []` / `NO-GO ['docs_checks']`); (f) required red pre-change. F-09 added. |
| PR-002 | MEDIUM | UNDER-SCOPE | A correctness / F silent failure | `docs_check.check_doc` "`read_text(encoding=\"utf-8\")`"; measured `UnicodeDecodeError` on a `\xff\xfe` doc | E-04 said a checker failure "must not be swallowed into a pass" but gave no mechanism; uncaught, it crashes `build_report` instead of failing one row. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 catches around the computed call only, fails with a distinct could-not-run detail; arm (g) and V-04 added; F-10 added. |
| PR-003 | MEDIUM | IN-SCOPE | Executability / stop condition | E-01(c) "returns ZERO findings"; shared checkout with concurrent `docs/` edits | Keying "dependency landed" on a zero total would block or mis-validate on any new genuine doc finding; the dependency should be checked by the plan's location plus the specific finding's absence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/V-01/gate check `t9lcdu` in `executed/` and absence of the `'aw router'` finding; other findings recorded, not a stop. |
| PR-004 | LOW | IN-SCOPE | G execution contract | Gate "POST-GATE LIFECYCLE" | No runner/`aw ipd finalize` ownership clause or scope-justification route; evidence could carry an absolute path; stale "no Readiness written" line; baseline failure names treated as fixed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Lifecycle/scope-reason clause added; evidence path relative; gate prose updated; executing-session baseline authoritative. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should a raising checker surface? | Fail the gate with a could-not-run detail | Propagate (crashes report); swallow to pass (greenwash) | measured `UnicodeDecodeError`; plan's own E-04 "must not be swallowed" | yes |
| D-2 | What proves `t9lcdu` landed? | Plan in `executed/` and `'aw router'` finding absent | Zero total findings (fragile under concurrent doc edits) | `aw find plans t9lcdu`; AGENTS.md shared-checkout section | yes |
