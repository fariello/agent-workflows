# Review findings: plan jj5ju1

- Subject-Id: jj5ju1
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `0e2d9f172`. The plan file was committed and byte-identical to
the lane input (`cmp` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author` reported `clean` (one advisory `IPD-C801`) before semantic review, and
`--phase review-finalize` reported `clean` with zero findings after revision, including after E-06/V-06
and E-07/V-07 were added. The plan is `- Kind: child`, so `IPD-S407` does not apply.

DEPENDENCY STATE AT REVIEW: `tr8ugt` is in `executed/`; `76ic0k` is `approved` and still in `pending/`, and
`tests/test_no_code_structure_pins.py` does not yet exist. The runner will hold this plan
`dependency-blocked` until `76ic0k` executes, which is correct.

THE DOMINANT FINDING WAS DEMONSTRATED, NOT REASONED. The detector E-01/E-02 specify (Arm A inline search in
the slice lower bound, Arm B a per-function name bound from a `.find`/`.rfind`/`.index`/`.rindex` call,
both with `upper is None`; split arm a constant index >= 1 over `split`/`rsplit` with a `#`-leading literal
separator) was driven over `tests/**/*.py` minus `tests/fixtures/` and `tests/benchmark_fixtures/`:
308 files, 6,743 function bodies, 15 slice hits plus the `t[idx:]` reconstruction site. Only 3 of the 15 are
sites the plan names. The rest:

```
tests/test_ipd_lifecycle_cli.py:3240                  B 'stdout[idx:]'                    (json.loads recovery)
tests/test_plan_review_feasibility_rule.py:168,184    B single_content[single_start:], long_content[long_start:]
tests/test_tabulated_test_convention.py:58,69,95      B content[p16_idx:], section_16[subheading_idx:], content[heading_idx:]
tests/test_v_item_demonstration_reachability.py:57,85 B content[start_idx:] x2
tests/test_v_item_evidence_durability.py:64,80,122,137 B content[start_idx:], section_g[bullet_idx:], content[start_idx:], section_a[bullet_idx:]
```

Three of those files were ABSENT at authoring HEAD `46cd2f8a5` (`git show 46cd2f8a5:<path>` fails), and the
feasibility file's two sites came from `045444d7c` (`k6t24p`), also after authoring. The plan's gate said
that a guard firing on an unpredicted site must STOP, while forbidding both exemption and conversion, so as
written the plan could not complete. Conversion feasibility was demonstrated before choosing that remedy:
each read was re-expressed with `support.section`/`support.final_section` against the live workflow and
documentation files and every anchor phrase each test asserts was still present (`feas-G ok`, `feas-A ok`,
`reach-G ok`, `reach-A ok`, `dur-G-bullet ok`, P16 `final_section` did not refuse, the `### ` subsection has
no following `### ` so `final_section` holds, CONTRIBUTING `## Authoring conventions` section non-empty).

The split-arm census re-ran at 53 sites; 8 heading separators, only one at index `[1+]`
(`tests/test_support_section.py` line 230, the F-04 contrast). Order 02 converted the other four tails. No
field delimiter begins with `#`, so the heading test's soundness claim still holds.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | Rubric D, G (executability); live-artifact re-derivation | detector run above; `tests/test_v_item_evidence_durability.py:64` `section_g = content[start_idx:]`; `git show 46cd2f8a5:tests/test_v_item_evidence_durability.py` fails | 11 marker-located section reads in four files landed after authoring and are flagged by the specified detector; the gate forbids exempting or converting them, so the plan is red on arrival with no permitted remedy | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-06/V-06 converting them onto the bounded helpers (feasibility demonstrated), added the four files to `Scope-Paths`, scoped the STOP clause to sites no E-03/E-04/E-06 names, and re-measured F-01 |
| PR-002 | HIGH | UNDER-SCOPE | Rubric D; E-03 exemption set | `tests/test_ipd_lifecycle_cli.py:3240` `idx = stdout.find("{")` then `json.loads(stdout[idx:])` | A JSON-recovery tail is flagged by Arm B and is not a section read; `json.loads` refuses trailing text itself (`JSONDecodeError: Extra data`), so bounding it would be wrong. The plan's exemption list had no entry for it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-03(d) exempting it with that reason; V-03's expected count updated to four slice exemptions plus the split-arm contrast |
| PR-003 | HIGH | IN-SCOPE | Rubric G (gate executability); validation requirement | plan OQ-02 and gate "REPORT the firing ... rather than editing it"; `76ic0k` E-01 flags `ast.parse`/`ast.walk` in every test file but its own; `- Item-Dependencies: executed:76ic0k` | With `76ic0k` executed first (required), its guard fires on this plan's new file, and the plan forbade the one-line allowlist fix, so the suite necessarily ends red and V-01's "showing it passes" cannot be satisfied truthfully | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-07/V-07 adding one `(path, reason)` entry, declared `tests/test_no_code_structure_pins.py` in `Scope-Paths`, revised OQ-02 and the gate paragraph |
| PR-004 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy; re-derivation convention | F-01, F-03, E-01, V-01, V-02 authoring figures (218 files, 5,444 functions, 12 heading separators) | Authoring counts were stale (review: 308 files, 6,743 functions, 8 heading separators with one tail) and E-01/E-02 expected outcomes asserted "zero unexempted violations" on the post-Order-02 tree, which is false until E-03/E-04/E-06 land | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a review re-measurement to F-01, annotated the figures with review values while keeping re-derivation as the bar, and rephrased the E-01/E-02 outcomes to the post-E-06 state |
| PR-005 | LOW | IN-SCOPE | Internal consistency | Scope check "No production module and no existing test is touched"; Deferred "This plan must not touch one"; gate "The two `Scope-Paths` entries" | E-03 already required exemption comments in three existing test files, contradicting "no existing test is touched", and the revisions widened the surface further | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Swept and reconciled the Scope line, Scope check, Deferred row, Proposed changes, and gate wording |
| PR-006 | LOW | IN-SCOPE | Citation convention (`IPD-C801`) | E-04 expected outcome `tests/test_ipd_authoring.py:279` | Bare line citation with no symbol | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-cited as `tests/test_ipd_authoring.py::_add_unassigned`'s `t[idx:]` |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The 11 post-authoring sites: convert in this plan, exempt them, or carry them in a new plan? | Convert in this plan (E-06). | Exempt: rejected, it institutionalizes exactly the defect the guard exists to stop. New carrier plan: rejected, this plan's guard cannot land green until they are converted, so a separate plan would have to precede it and add a dependency for ~11 one-line conversions already demonstrated safe | detector run and conversion demonstration in Round 1 prose; plan gate "DO NOT WEAKEN THE GUARD" | yes |
| D-2 | The JSON-recovery tail: exempt, or narrow the detector to literal heading markers? | Exempt per site (E-03 d). | Narrowing to literal `#` markers: rejected, Arm A/B markers are commonly held in names (`start_heading`, `pol.SUMMARY_HEADER`, `RC.REPORTING_SECTION_TITLE`), so a literal-only test would blind the guard to most real sites | `tests/test_v_item_evidence_durability.py` `start_idx = content.find(start_heading)`; `tests/test_defect_report.py` `prompt.find(RC.REPORTING_SECTION_TITLE)` | yes |
| D-3 | The `76ic0k` interaction: keep "report and let a human decide", or make the one-line allowlist edit here? | Make the edit (E-07), declared in `Scope-Paths`. | Report only: rejected, it guarantees a red suite at plan end. Widening `76ic0k`'s structural self-exclusion: rejected for the reason OQ-02 already records | `76ic0k` E-01/E-02 text; AGENTS.md validation requirement; plan-review scope-fence ruling (declare and justify rather than stop) | yes |

No `Reversible: no` decision was taken. OQ-01, OQ-02 and OQ-03 are `resolved` and `Blocking: no`; OQ-02's
resolution was revised in place for PR-003. No finding was left `OPEN` or `DEFERRED`, so no escalation is
required. Execution remains correctly gated on `76ic0k` reaching `executed`.
