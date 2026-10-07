# Review findings: plan xtensb

- Subject-Id: xtensb
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `a93c72277`. The plan was committed and byte-identical to the lane input, so no pre-review
snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and
`--phase review-finalize` was clean (no findings) after revision.

Re-verified:
- S1: `def should_unicode` is at `agent_workflows/term.py:940`; spec A12 cites `term.py:374`.
- S2: `docs/cli-output-contract.md:225` is `- **Completeness and Verification**:`; section 9 heading at line 299, retracted quote at 304.
- S3: `accessibility.md:56-63` now reads "DEGRADE THROUGH 256 -> 16 -> NONE (DECISIONS D42)".
- S4: walking `cli._build_parser()` (group = parser carrying a subparsers action): 252 leaves, 34 groups, 286 nodes, 29 leaves declare neither flag (`__complete`, `run/as`, `run/ipd`, host-driver leaves).
- F4: `docs/cli-output-contract.md` 1.1 row 2 states the falsey rule and names `term._force_color_is_forcing`.
- NEW S6: spec Section 12a point 3 cites `docs/cli-output-contract.md:159-163`; at HEAD those lines are `---` and `## 3. Exit Code Semantics`.
- Offset grep over the spec returned five `path:line` tokens; the plan's sweep had checked symbols and paths only.
- `lifecycle_style.STAGES` is a `MappingProxyType`; `GLYPH_BLOCKED`/`GLYPH_RECOVERING` carry U+FE0E; `resolve` takes only family, native_status, activity, integrity, obstruction, condition.
- `aw specs note` takes a `path` positional and `--message`.
- `tests/test_lifecycle_style.py tests/test_term.py`: 43 passed. Backlog `nzqj6m` graduated; OQ-01 carrier `0rnvj6` exists (open).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Spec sync / evidence | spec Section 12a point 3 "as `docs/cli-output-contract.md:159-163` promises"; `docs/cli-output-contract.md:159-163` = `---`, `## 3. Exit Code Semantics` | A sixth stale offset was missed because the sweep resolved symbols and paths but never `path:line` offsets; the plan's "zero unresolvable" bar would have passed with it live. | all Low | FIXED | E-01 adds S6 and an offset-grep sweep method; Findings table gains S6; V-01 and Proposed changes cover it; A12's historical offset explicitly left alone. |
| PR-002 | LOW | IN-SCOPE | E. Verification | `cli._build_parser()` walk at review: 252/34/286 vs plan's 250/35/284 | Census drifted between authoring and review; the group/leaf definition was unstated so a re-measure could count differently. | all Low | FIXED | E-02 states the counting definition, records both measurements, forbids an "always 29" claim. |
| PR-003 | MEDIUM | IN-SCOPE | E. Reachability | `agent_workflows/lifecycle_style.py:262` `STAGES = _build_stage_table(...)` returns `MappingProxyType` | V-04's counterfactual "local patch of the stage table" is not reachable in place; E-04 did not name the public accessors. | all Low | FIXED | E-04 names `style_for`/`glyph_for`, how to build `Resolved` per stage, and a `mock.patch.object` probe; V-04 updated. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing | `lifecycle_style.resolve` signature; E-05 (b) | E-05(b) is vacuous by construction: a resolver never handed work-kind cannot vary on it, so the "backlog item whose record carries a differing Work-Kind" leg tests nothing. | all Low | FIXED | E-05 adds (c), two backlog items differing only in `Work-Kind` rendered through a real `find` consumer with identical lifecycle tokens asserted; V-05 demands it. |
| PR-005 | LOW | IN-SCOPE | G. Live-artifact bar | V-07 "no regression against the 43 and 105 baselines" | Test counts used as the bar. | all Low | FIXED | Bar is now zero failures vs an executor-measured baseline by name; counts kept as context. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | Approval gate; E-06 | No scope-fence declaration, no runner-vs-hand finalize ownership, no hands-off for `nzqj6m`/spec status; E-06 omitted that `aw specs note` takes a path. | all Low | FIXED | Gate paragraph added; E-06 names the path form and four re-pointed citations. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should A12's historical `term.py:224-227` be rewritten too? | No, it is marked history | Re-point it | Spec A12 "Only the CITATION was stale. This line read `term.py:224-227`" | yes |
| D-2 | Fix S6 in this plan rather than file a new item? | Yes | File backlog | Same defect class and same file the plan already amends | yes |
