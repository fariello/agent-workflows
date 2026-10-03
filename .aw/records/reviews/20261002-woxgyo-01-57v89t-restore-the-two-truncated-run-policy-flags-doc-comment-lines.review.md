# Review: Restore the two truncated RUN_POLICY_FLAGS doc-comment lines

- Subject-Id: 57v89t
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `dd8001247`:

- `#: #: Active runner conflict resolution modes.` is the only `#: #:` site in `agent_workflows/*.py`.
- `git show 7dd1c486c` has a first hunk that turns the two `-#: types, ...` / `-#: therefore ...` lines into the one `+#: #:` line. `git log -L` gives `7dd1c486c` and then `b9751fadf`.
- Both lines can be recovered verbatim from `7dd1c486c^`, at 100 and 75 characters.
- `run_selection_policy.RUN_MIXED_TYPES = "RUN-MIXED-TYPES"` is live.
- The `ON_INTEGRATION_BLOCKED_*` precedent is present.
- Local ruff is 0.16.3, while the pin is v0.4.4. The local version already reports 3 hunks, all far from the region.
- `8wpjeq` E-04(a) explicitly forbids touching this damage.

I re-ran the relocation shape against the real file in memory. It produced `AST EQUAL True` under `include_attributes=False`. My adjacency enumeration counted 221 of 221 `#:` blocks immediately followed by a top-level statement. The plan's 214 used a different counting method, and the plan already treats that count as context only.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Validation honesty (E) | plan E-04(a), V-04(1) "parse `git show HEAD:agent_workflows/runner_shared.py`" | The AST proof compares against a symbolic `HEAD`. Once the edit is committed, `HEAD` contains it, so the check can report EQUAL without checking anything. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now records the pre-edit SHA as `<base>`, and E-04(a) and V-04(1) compare against `<base>`. |
| PR-002 | MEDIUM | IN-SCOPE | Live-artifact criteria (G) | plan E-03 expected outcome and V-03(3) "still returning `7`"; sibling `8wpjeq` exists to remove those citations | The bar is a fixed count of a live artifact that a sibling plan exists to reduce. If `8wpjeq` lands first, a correct execution FAILS V-03. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 records the pre-edit count as `<cites>`, and the bar is now equality with `<cites>`. The value 7 is kept as context. |
| PR-003 | LOW | IN-SCOPE | Evidence accuracy | plan E-02 "(65 references, more than every other file combined)"; measured `grep -o ON_CONFLICT\w*`: runner_shared 37, config.py 19, tests/test_runner_active_conflict.py 15 | The reference count is wrong, and the "more than every other file combined" claim is false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with an accurate description that does not depend on a count. |
| PR-004 | LOW | IN-SCOPE | Validation feasibility (E) | plan E-04(c); current `ruff format --diff` headers `@@ -34734,9`, `@@ -35222,9`, `@@ -36962,7` | The restoration adds net lines, which shifts every downstream hunk header. A raw before/after comparison of the formatter output would therefore report a spurious change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04(c) now compares hunk bodies with the `@@` headers stripped. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep OQ-01's relocation of the `ON_CONFLICT_*` group above the `RUN_POLICY_FLAGS` doc-comment? | Keep it | In-place restore only, which leaves a detached `#:` block | Review prototype gave `AST EQUAL True`; adjacency holds for 221/221 blocks; `ON_INTEGRATION_BLOCKED_*` shape at `agent_workflows/runner_shared.py` `ON_INTEGRATION_BLOCKED_DEFER` | yes |
| D-2 | What should the sibling-citation bar be? | Equality with the count measured before the edit | A fixed `7` (fails if `8wpjeq` lands first); dropping the check (loses the proof of separation) | `8wpjeq` E-04 scope | yes |
