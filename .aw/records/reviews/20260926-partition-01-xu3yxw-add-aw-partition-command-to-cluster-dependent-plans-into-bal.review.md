# Review findings: plan xu3yxw

- Subject-Id: xu3yxw
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-001 | high | IN-SCOPE | G (executability) | `agent_workflows/selectors.py` defines `resolve` and `resolve_selectors` only | The plan named `selectors.resolve_selector` and `selectors.resolve_artifact_by_id`, which do not exist. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | E-03 uses `selectors.resolve_selectors` and `attention.scan`; F-5. |
| PR-002 | high | IN-SCOPE | A / C | `runner_shared.queue_sort_key` ("DECLARED EDGES WIN ... `dependency_depth` stays FIRST"); `classify_drain_block` external edge PERMANENT | The head/tail buffering rule for oversized components cannot work: the runner re-sorts each queue by dependency depth, and a cross-shard dependent fails at drain wherever it sits. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | E-02 splits in depth order and REPORTS every cut edge; OQ-02 revised; F-7. |
| PR-003 | high | UNDER-SCOPE | C / G | `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`; `command_surface.COMMAND_INVENTORY` | A new verb must be declared in the command inventory; `command_surface.py` was not in Scope-Paths, so the conformance test would fail. | C:Low;U:Low;S:Low;F:Medium;Overall:Low | fixed | E-05 declares it; Scope-Paths extended; F-8. |
| PR-004 | medium | IN-SCOPE | C | `attention._extract_item_dependencies` calls the public `ipd_schema.parse_item_dependencies` | The plan called the private `_parse_item_dependency_edge` although parsed edges already exist on `attention.Item`. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | E-01 works over `attention.Item`; F-6. |
| PR-005 | medium | IN-SCOPE | A / F | `cli` "aw run as <profile> [SELECTOR ...] the profile decides the host"; `runner_profiles` stores a runner per profile | `aw oc run as <profile>` can pair an agy profile with the oc host. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | `--as` emits host-neutral `aw run as`; `--as` with `--run oc` or `--run agy` refused; OQ-01 revised; F-9. |
| PR-006 | medium | IN-SCOPE | F (silent failure) / B (input) | `attention.parse_priority_filters` comment ("silently returned 0 items"); `aw oc run` with no selector means `all` | Implicit piped-stdin detection can hang on an inherited terminal; an empty shard would print a bare run command meaning `all`; priority must be validated; unknown stdin ids were silently dropped. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Explicit `--stdin`; empty shard prints nothing; validated priority; unknown ids reported; F-10. |
| PR-007 | medium | OVER-SCOPE | G | spec `z7nbn1` 4.1 "THE QUEUE ADMITS ONLY PLANS"; `build_dynamic_manifest` compiles `discover_plans` alone | `-t/--type` and the `batch` alias add surface nothing needs; runners cannot dispatch non-plans. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Both removed; non-plan partitioning deferred with reason; F-11. |
| PR-008 | low | UNDER-SCOPE | E / G (execution contract) | original gate section | Missing determinism, read-only proof, JSON contract, empty-selection behavior, CHANGELOG, and the gate's execution-contract elements. | C:Low;U:Low;S:Low;F:Low;Overall:Low | fixed | Added to E-02, E-05, E-06 and the gate; F-12. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | How should an oversized component be split? | Depth-ordered placement plus reporting every cut edge | Head/tail placement (author); refusing to partition | `runner_shared.queue_sort_key` re-sorts by depth, so placement order is discarded; reporting is the only lever the operator can act on | yes |
| D-2 | How should `--as <profile>` be emitted? | `aw run as <profile> <ids>` | `aw <run> run as <profile>` (author) | profiles carry their own runner (`runner_profiles`); `aw run as` is the documented host-neutral route | yes |
| D-3 | Should stdin be auto-detected? | No, explicit `--stdin` | `not sys.stdin.isatty()` detection | a scripted call with an inherited non-TTY stdin would block; `ttywedge` g40w37 measured a 1h49m wedge from an inherited stdin | yes |
| D-4 | Keep the `batch` alias and `-t/--type`? | Remove both | Keep as authored | runners dispatch plans only (spec `z7nbn1` 4.1); an alias is a second public name with no requirement behind it | yes |
