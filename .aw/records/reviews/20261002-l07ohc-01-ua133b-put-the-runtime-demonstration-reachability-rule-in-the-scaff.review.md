# Review findings: plan ua133b

- Subject-Id: ua133b
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in lane `review-sweep-run-20261007T032752Z-4094028` at HEAD `ca03f0c56`. The plan was committed (`949392c2a`) and byte-identical to the sealed lane input (rev-8); no snapshot needed. `- Kind: child`, so `IPD-S407`/`IPD-S408` do not apply. `aw ipd lint --phase author` clean before review.

Re-verified: both review bullets extracted at 1846 characters each and equal; `_VALID_INTRO in _AUTHORING_PLACEHOLDERS` is False; `"  - Required evidence: TODO falsifiable evidence." in _AUTHORING_PLACEHOLDERS` is True; `_VALID_INTRO` is unchanged from the plan's quote (no reachability sentence yet); `tests/test_v_item_demonstration_reachability.py` has exactly two tests and the `REACHABILITY_ANCHOR_PHRASES` list; `tests/test_ipd_templates.py` fixed argument set matches E-03; `ScaffoldVocabularyIntroTests` locator and regex as quoted; `build_skeleton` signature accepts the listed arguments; `tests/test_ipd_templates.py tests/test_v_item_demonstration_reachability.py` -> `12 passed`. A real `aw ipd scaffold --kind child ... --path /tmp/opencode/<grammar-name> --apply` wrote the file with the current intro; `aw ipd lint --phase author` reported `advisory` (`check.ipd-dependency-unresolved`, from `- Item-Dependencies: unresolved`), exit 0; scratch file removed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E reachability of evidence | V-04(b) "run `aw ipd lint` on that file and paste its `conforming` disposition"; measured CLI disposition `advisory` with `check.ipd-dependency-unresolved` on a fresh scaffold | The demanded observation is unreachable as worded: a fresh scaffold never lints `conforming` through the CLI, so an honest executor would have to fail V-04. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04(b), Required tests and E-02's expected outcome now demand an exit-0 CLI record (advisory expected) plus `ipd_lint.lint_text(..., checkpoint="author", directory="pending").disposition == conforming`, the call `TemplateLintTests` already makes; scratch path placed outside the repo. |
| PR-002 | LOW | IN-SCOPE | Live baseline | F-08 three failing node ids; commit `8c460a9a1` "Fix baseline test failures on main ..." | The named baseline failures may already be fixed, so V-03(d) compared against a stale set. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03(d) compares against a failing-node-id baseline captured at execution; F-08 marked as context. |
| PR-003 | LOW | IN-SCOPE | Stale evidence / cross-plan handoff | `ezv744` backlog is `graduated`; plan `5q9a6a` is `approved`; its Deferred row on the Section 14 refresh carries `- Carrier: l07ohc` | The plan described `ezv744` as open and did not respond to the sibling's handoff of the Section 14 refresh onto `l07ohc`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-06 and Deferred updated to `5q9a6a`; Spec sync now records an explicit Carrier-Declined for the Section 14 refresh (D-2), so the handoff does not dangle. |
| PR-004 | MEDIUM | IN-SCOPE | G execution contract | Gate "Execution runs through `aw ipd begin` and terminates through `aw ipd finalize`" | Unconditional begin/finalize instruction; no runner-ownership condition, no scope-fence declaration, no backlog close. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now: runner owns the transition in a lane; by hand `aw ipd begin ua133b` / `aw ipd finalize ua133b ... --apply`; scope fence with `--scope-reason`/`--scope-ack`; `l07ohc` close after execution. |
| PR-005 | LOW | IN-SCOPE | Open questions / editorial calls | OQ-01 `- Status: open`, `Owner: reviewer`; Deferred CHANGELOG row "flagged for a reviewer to overrule" | Two questions explicitly addressed to the reviewer were left open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved NO (D-1); CHANGELOG settled as no entry (D-3). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should `assess.md` also state the reachability obligation (OQ-01)? | No | Yes, one clause, as `por1hi` did for right-sizing | `assess.md` `## The IPD you produce` defers item shape to `templates/ipd.md`; generator comment "ONE LINE ON PURPOSE"; right-sizing is section-level, reachability is per-`V-*` | yes |
| D-2 | Should this plan accept `5q9a6a`'s handoff of the spec Section 14 example refresh onto `l07ohc`? | Decline, recorded as Carrier-Declined | Add the spec to Scope-Paths and refresh the fenced example | `5q9a6a` calls it "a deliberate reviewer call"; Section 14 example is illustrative, not byte-pinned, and already lacks the `uh9jsk` vocabulary clause | yes |
| D-3 | Add a `CHANGELOG.md` entry? | No | One line under Changed | `uh9jsk` and `9aprci` added none for the same constant and rule; audience is an authoring agent | yes |
