# Review findings: plan i00j2o

- Subject-Id: i00j2o
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `24f9f0cf3`. The pending plan matched the sealed lane input byte for byte and was already committed, so no snapshot commit was needed. `aw ipd lint --phase author` reported `clean`. `- Kind: child`.

The cited symbols resolve: `cli._run_find` (the "Validate --limit upfront" block, the `--paths` branch `for p in all_paths: print(p)`, the agent branch `next_parts` / `_sanitize_for_next` / `render_stream` call, the human `for line in all_lines: term.line(line)` loop with the paw8so comment "it never removes, reorders or suppresses a result"), the shared `"Max rows (index/find)."` declaration, `renderers.AgentRenderer.render_stream` (`limit = ctx.limit`, `next_template.format(limit=tot)`), `Term.status` / `Term.next_action`, `docs/cli-output-contract.md` Section 12 bullets, and the harness `tests/test_find_agent_stream.py` `run_find`. The four named test modules exist; `tests/test_find_human_limit.py` does not yet. Backlog `no88yi` is `graduated` with `Blocks-Release: next`, matching the plan.

Live re-measurement: `aw find plans`, `--limit 3`, `--limit 3 --paths` each 1441 lines; `--agent --limit 3` summary `total 1441, emitted 3, omitted 1438`; `--limit 0 --paths` refuses at exit 2; `--paths` versus `--agent` path order over `find all` is identical. A fixture probe through the `test_find_agent_stream` setUp showed `find all col001 --no-color --limit 1` prints both rows and the collision warning (defect present on the selector + collision path), and `find plans --no-color --limit 2` prints all 3 rows.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | D / E (invariant without test) | `agent_workflows/cli.py:14204` comment "EVERY MATCHING ROW IS PRINTED FIRST AND THE WARNING FOLLOWS"; `tests/test_find_agent_stream.py:87` `col001` collision fixture | E-03 and OQ-02 decide that the id6-collision warning is computed over the full set and printed after the notice, but no E-01 assertion pins it, so an executor could bound or reorder it silently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-01 assertion (9) over the existing `col001` fixture (1 row, notice, Next, then warning naming both claimants); V-03 demands it GREEN. |
| PR-002 | MEDIUM | IN-SCOPE | A / F (escaping correctness) | `agent_workflows/cli.py:14064` `_sanitize_for_next` returns `quoted.replace("{", "{{")`; `agent_workflows/renderers.py:335` `next_template.format(limit=tot)`; `tests/test_find_agent_stream.py:238` `test_09` | E-02 said the human path appends without brace escaping but left the helper's escape behaviour unspecified; factoring `_sanitize_for_next` as-is would print `{{x}}` in the human `Next` line, an unrunnable command. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now makes escaping a caller choice (agent escapes, human and `--paths` do not) and keeps the same flag set; added E-01 assertion (10) for a `{x}` / `has space` selector, demanded in V-03. |
| PR-003 | LOW | IN-SCOPE | C (one canonical source) | `agent_workflows/result_types.py:101` `select_output` parses `args.limit` into `ctx.limit`; `agent_workflows/renderers.py:328` `limit = ctx.limit` | E-03/E-04 named a `limit` variable without its source; re-parsing `args.limit` would create a second path that could diverge from the agent surface. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and E-04 now read `ctx.limit`. |
| PR-004 | LOW | IN-SCOPE | G (live-artifact counts; deferred coverage) | Review-lane runs: 1441 vs plan's 1414/1415; `aw find plans --max-depth 0 --agent --limit 1` reports `total 1441`; agent `next_parts` omits `--max-depth` / `--include-ignored` | Authoring counts drifted (property unchanged), and the continuation builder E-02 reuses silently drops the two `find`-only traversal flags, which the plan neither stated nor deferred. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-07 recording the re-measured counts as context only, and a `Carrier-Declined` deferred row for the traversal flags with the measurement that no observed case changes the listed set. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the continuation carry `--max-depth` / `--include-ignored`? | No; preserve today's agent `next` bytes and record a declined deferral. | Add both flags to the shared builder for every surface. | Plan BOUNDARIES forbid changing `--agent` bytes; review measurement shows `total` unchanged under both flags on this repository. | yes |
| D-2 | Should brace escaping live in the helper or the caller? | Caller-controlled flag on the helper. | Two separate builders; post-hoc unescape on the human path. | `renderers.AgentRenderer.render_stream` formats only the agent template; one builder avoids query-reconstruction drift (plan F-06). | yes |
| D-3 | Where does `limit` come from on the new surfaces? | `ctx.limit`. | Re-parse `args.limit`. | `result_types.select_output` already parses it and the agent surface reads it there. | yes |
