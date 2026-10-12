# Review findings: plan mq715m

- Subject-Id: mq715m
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `613ce0471` in an isolated review lane; plan committed and unchanged (last touched by
`753360827`), no snapshot needed. `aw ipd lint --phase author --agent` clean before semantic review.

Re-verified:
- 12 `*.golden` files, all under `tests/fixtures/conformance_goldens/`; no `*.snap*`/`*snapshot*` under `tests/`.
- No golden contains `\u26a0\ufe0f`, `\u21a9\ufe0f`, or bare `\ufe0f` as code points; no golden contains any `\u` escape text.
- `CriterionA5VariationSelectorTests` exists in `tests/test_lifecycle_style.py` with one method covering constants,
  `MULTI_CODEPOINT_GLYPHS`, and rendered output; it reads no file. Module already imports `Path` and `mock`.
- `Term.format_lifecycle_marker` / `Term.style_lifecycle_text` in `agent_workflows/term.py`; `STAGE_ORDER` in
  `agent_workflows/lifecycle_style.py`.
- Spec A5 line text matches E-02's quote; spec is `approved`, `Blocks-Release: next`; precedent `aw specs note`
  history line dated 2026-10-08 exists. `aw specs note` takes `path` positional and `--message`.
- `JsonRenderer.render` in `agent_workflows/renderers.py` uses `json.dumps(..., indent=2)` (default
  `ensure_ascii=True`); `json.dumps("\u26a0\ufe0f")` prints the ASCII escape `"\u26a0\ufe0f"`.
- `_read_or_write_golden` / `AW_CONFORMANCE_UPDATE_GOLDENS` in `tests/test_cli_quality_gates.py` as cited.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D. Anti-regression | `agent_workflows/renderers.py` `JsonRenderer.render` `json.dumps(result.to_dict(), indent=2)` | A literal-code-point scan is blind to the 4 `*.json.golden` files: with default `ensure_ascii=True` an emoji is committed as `\u26a0\ufe0f` escape text, so the exact regeneration hole the plan exists to close stays open for one third of the corpus. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now scans both the literal and the case-insensitive JSON escape forms; Expected outcome, E-02's referent (b), and V-01 (new counterfactual 1b on `x.json.golden`) updated; F2 records the review re-measurement. |
| PR-002 | LOW | IN-SCOPE | E. Testing | E-01 / V-01 `mock.patch.object` on the discovery-root constant | The counterfactual only bites if the test reads the module global at call time; binding it as a default argument or class attribute would make the patch inert and the counterfactual vacuous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 states the root must be read from the module global inside the method. |
| PR-003 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked an OQ status statement, scope-as-declaration (`--scope-reason`/`--scope-ack`), the hard-MUST paste rule, and conditional runner/executor finalize ownership (it named `aw ipd finalize` and runner self-finalize without saying who). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten as a bulleted execution contract with all elements. |
| PR-004 | LOW | IN-SCOPE | Q. Open questions | OQ-01 `- Owner: none` on a resolved, author-decided question | A resolved question decided on the author's authority should record that owner, not `none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner set to plan author, confirmed by review D-1; resolution notes the review kept both routes. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Take both closing routes of backlog `0rnvj6`, or rule rendered output is the whole A5 obligation? | Both (scan committed `*.golden` + amend A5) | Narrower ruling only (leaves regeneration hole); building a lifecycle snapshot corpus (new infra no criterion needs) | backlog `0rnvj6` "WHAT WOULD CLOSE IT"; `tests/fixtures/conformance_goldens/` exists; `_read_or_write_golden` regeneration path | yes |
| D-2 | Scan JSON goldens for escape text too, given A5 names glyphs not escapes? | Yes, both spellings of the two named sequences only | Literal-only scan (blind on JSON goldens); bare `U+FE0F`/`\ufe0f` ban (new requirement) | `JsonRenderer.render` default `ensure_ascii=True`; review probe of `json.dumps` | yes |
