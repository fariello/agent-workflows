# Review: Record the runtime-demonstration reachability property of Required evidence in spec Section 5.4

- Subject-Id: 5q9a6a
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so I skipped the pre-review snapshot. `aw ipd lint --phase author` and `--phase review-finalize` were both clean.

I re-verified the following at lane HEAD `7f2973fc1`:

- **Review bullets.** The bullet beginning `- **Runtime-demonstration reachability` is 1846 characters in both `plan-review.md` and `review-rubric.md`, and the two strings are equal.
- **Section 5.4.** The section text matches F-02: definition, five-item list, durability paragraph, `Observed evidence:` paragraph, then the closing sentence "The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient."
- **`reachab` occurrences.** There is exactly one, in Section 9.2, and it uses typographic quotes (`“unreachable”`).
- **Contended set.** The nonterminal plans declaring the spec path in `- Scope-Paths:` are exactly `0nxa8o` (`approved`) and `fhinri` (`to-review`). The `0nxa8o` E-04 does add a Section 5.4 statement.
- **Spec workflow history.** There are five `note (aw specs)` records and none for `vtup6x` (F-06).
- **Spec check.** `aw specs check <spec> --json` reports `clean`.
- **Test modules.** Each target test module currently holds 2 tests. The `ua133b` Scope-Paths declare `tests/test_v_item_demonstration_reachability.py` and no spec.
- **Supporting tests.** All cited supporting test files exist.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Internal consistency (G) | plan `## Proposed changes` item 1: "the empty set of nonterminal plans declaring this spec path" vs F-08 / E-01(d) | Proposed changes still states the first draft's false "empty set" claim, which F-08 itself refuted. A sweep miss. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now names the two plans and cites F-08. |
| PR-002 | MEDIUM | UNDER-SCOPE | Sequencing composition (A, D) | `0nxa8o` E-04 "In Section 5.4, state that a multi-line pasted transcript is the EXPECTED shape for command evidence"; plan E-02 placement and E-02 expected outcome | The plan depends on `0nxa8o` landing first, yet its placement rule and its "byte-unchanged" preservation list assume the authoring-time Section 5.4. They do not say where the new paragraph goes when `0nxa8o` has inserted text, or that `0nxa8o`'s text must also survive unchanged. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now places the paragraph immediately after the durability paragraph even when `0nxa8o` has inserted text, and records the resulting order in V-02. The expected outcome now also preserves `0nxa8o`'s landed text. |
| PR-003 | MEDIUM | IN-SCOPE | Live-artifact criteria (G) | Required tests "compared to the F-07 baseline BY NODE ID"; V-04(b) "compare ... against the F-07 baseline" | The comparison bar is a failure set measured at authoring time, and that set will drift. The same section also requires an in-lane baseline, so the two instructions contradict each other. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both places now compare against the in-lane pre-edit baseline. F-07 is context only. |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract (G) | gate "is NOT auto-run"; "Execution runs through `aw ipd begin` and terminates through `aw ipd finalize`" (unconditional) | Two problems in the gate. First, "NOT auto-run" contradicts the gate's own reliance on runner-enforced `Item-Dependencies`. Second, it instructs finalize unconditionally, with no runner/executor ownership and no scope-fence declaration semantics. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now states conditional ownership (runner vs manual) and the scope fence with `--scope-reason`/`--scope-ack`. It keeps the design-collision STOP and frames it as a genuine-unsafe stop, not a scope stop. |
| PR-005 | LOW | IN-SCOPE | Executability (G) | spec line in Section 9.2 `“unreachable”` (U+201C/U+201D); plan Deferred CHANGELOG "flagged for a reviewer to overrule" | Grepping with ASCII quotes would miss the Section 9.2 sentence. Separately, the CHANGELOG question was left for the reviewer to settle. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a quote-character note to E-02. The CHANGELOG question is settled as "no entry" (D-2). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the new paragraph go when `0nxa8o` has landed Section 5.4 text? | Immediately after the durability paragraph, ahead of `0nxa8o`'s text | After `0nxa8o`'s text (would separate the two properties of the demand) | plan E-02 placement rationale; `0nxa8o` E-04 concerns `Observed evidence:` shape | yes |
| D-2 | Does this amendment need a CHANGELOG entry? | No | Add one (the audience is IPD authors, not CLI users) | `vtup6x` declared none for the sibling amendment to this same section | yes |
| D-3 | Should OQ-01 (adding the text to the companion `ipd-spec`) stand as resolved? | Keep it resolved: no | Add a pointer sentence | `ipd-spec` points to rubric G rather than restating it, as the plan's OQ-01 records | yes |
