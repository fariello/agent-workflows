# Review findings: plan okiso1

- Subject-Id: okiso1
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `63541d1ff`. The plan was committed and byte-identical to the
lane input (`cmp`), so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean with zero
findings before review and `--phase review-finalize` clean with zero findings after revision. `- Kind:
child`, so `IPD-S407` does not apply.

Verified as claimed: the bare-path branch `if getattr(args, "paths", False) or (ctx.is_agent and all_paths):`
and its comment in `cli._run_find`; the `--paths` exit expression `return 0 if (all_paths or not selectors)
else 1`; `_FIND_ID6_COLLISION_RULE = "find.id6-collision"`; the two `rel_p = str(e.path)` fallbacks in
`_find_type_records`; `render_stream` as the sole `ctx.limit` reader with zero production callers;
`agent_schema.normalize_repo_path` exists; a summary carrying `diagnostics` validates (`[]`); the
`docs/cli-output-contract.md` Section 12 bullets, the `docs/cli-human-guide.md` row, the
`docs/cli-agent-protocol.md` worked summary, and the `docs/cli-migration.md` recipe text; all five named
existing `find` test modules and all five carrier backlog items exist.

Measured at review, in process, and NOT anticipated by the plan:

```
render_summary("find",3,1,2,context=<fields=['path']>,next_cmd="x")
  -> {"schema":"aw.agent/v1","kind":"summary","cmd":"find","outcome":"clean","exit":0,"total":3,"emitted":1,"omitted":2,"complete":true}
render_stream([...2 items...],"find",context=<fields=['path'],limit=1>,next_template="aw find plans --agent --limit {limit}")
  -> item {"path":"a"}; summary {...,"total":2,"emitted":1,"omitted":1,"complete":false}   # no "next"
"aw find plans {x} --agent --limit {limit}".format(limit=3) -> KeyError: 'x'
aw find plans zzzzzz --agent -> {"kind":"result","cmd":"find",...,"evidence":["find-count"],"next":"aw find plans"}
```

`render_summary`/`render_stream` have no `diagnostics` parameter, and `agent_schema._PRESERVED_FIELDS` is
`_MANDATORY_FIELDS | {"applied","total","emitted","omitted"}`, so `next` and `diagnostics` are projected away.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric G (reachability); A | `renderers.AgentRenderer.render_summary` fixed key set; plan E-03 "CARRY THE `find.id6-collision` FINDING INTO THE `summary` RECORD'S `diagnostics`" while Scope check said "`renderers.py` is NOT edited" | The renderer cannot emit `diagnostics`, so E-03 was unreachable within declared scope except by hand-building a record (the `enygec` defect class) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 adds an additive `diagnostics` keyword to `render_summary`/`render_stream`; `agent_workflows/renderers.py` added to `Scope-Paths`; Scope check corrected |
| PR-002 | HIGH | IN-SCOPE | Rubric D/E (the fix re-breaks under its own flag) | measurement above: projected summary loses `next` | `--limit N --fields path` would emit `complete:false` with no continuation command, so the guide row the plan fixes stays false under `--fields`, and the collision diagnostic would vanish too | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 makes the summary retain `next` and `diagnostics` under projection, in the renderer and not in `_PRESERVED_FIELDS` (D-2); E-01 assertion (7) and V-03 evidence added |
| PR-003 | HIGH | IN-SCOPE | Rubric B (input reaching `str.format`); E | `render_stream` `next_template.format(limit=tot)`; `KeyError: 'x'` above | A selector carrying a brace crashes the stream; a selector with a space yields a non-runnable `next`. E-04 covered only home paths | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 requires brace escaping and `shlex.quote` of selectors; E-01 assertion (9) and V-04 evidence added |
| PR-004 | MEDIUM | UNDER-SCOPE | Rubric D (shape consistency); boundary with `zyj8io` | `aw find plans zzzzzz --agent` emits a `result` record | The plan did not say what a zero-match `--agent` query emits after the change, leaving two shapes under one flag (the Concern's own complaint) and the protocol doc's zero-match `find` example unreconciled | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | One shape: `--agent` always streams; zero matches emit a lone `summary` at the same exit code; `--json` unchanged; E-06 reconciles the doc example; Deferred notes the impact on `zyj8io` E-04 |
| PR-005 | MEDIUM | IN-SCOPE | Evidence accuracy (F-09) | `BaseRenderer.emit` catches `BrokenPipeError` only for a `CommandResult`; `render_stream` returns a string | The incidental broken-pipe fix claimed in F-09 does not happen unless the call site writes inside a guard | all Low | FIXED | E-03 requires a guarded write; F-09 corrected; E-01 assertion (10) and V-03 evidence added |
| PR-006 | MEDIUM | UNDER-SCOPE | Execution contract | gate | No scope-fence declaration; lifecycle lacked conditional runner/executor ownership of `aw ipd finalize` | all Low | FIXED | Added SCOPE FENCE paragraph and conditional-owner lifecycle; noted the `Blocks-Release` handoff for `wdazvp` |
| PR-007 | LOW | IN-SCOPE | Evidence currency; OQ owner field | Deferred `qm04zi` row says `c4btis` is `to-review`; it is in `executed/` and `qm04zi` is `done`; OQ `- Owner: none` | Stale status; resolved OQs recorded no owner | all Low | FIXED | Updated the row; OQ owners set to `plan author` |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `diagnostics` reach the summary record? | Additive keyword on `render_summary`/`render_stream`. | Hand-build the summary in `cli.py`: rejected, it is the `enygec` hand-built-record defect class | `renderers.AgentRenderer.render_summary`; backlog `enygec` | yes |
| D-2 | Where should `next`/`diagnostics` survive `--fields`? | In `render_summary`, for summary records only. | Widen `agent_schema._PRESERVED_FIELDS`: rejected, the flat union would retain `next` on every `result` record of every command | `agent_schema._PRESERVED_FIELDS` comment ("Preserving a flat union rather than a per-kind mapping") | yes |
| D-3 | What does a zero-match `--agent` query emit after the change? | A lone `summary` (`total: 0`) at the unchanged exit code. | Keep the `result` record: rejected, two shapes under one flag is what the Concern complains of, and `docs/cli-migration.md` tells scripts to stop at the `summary` | plan Concern; `docs/cli-migration.md` recipe 4 | yes (unshipped surface, F-05) |

No `Reversible: no` decision. OQ-01..OQ-03 are `resolved` and `Blocking: no`. No finding is left `OPEN` or
`DEFERRED`. D-3 should be reflected in `zyj8io` at its next review (noted in this plan's Deferred section).
