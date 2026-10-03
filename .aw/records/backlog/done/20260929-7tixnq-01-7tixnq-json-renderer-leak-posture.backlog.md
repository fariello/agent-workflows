- Id: 7tixnq
- Status: done
- Graduated-To: 7tixnq
- Set: 7tixnq
- Priority: medium
- Work-Kind: chore
- Summary: JsonRenderer emits an unsanitized machine-local home path because the --json surface never runs the aw.agent/v1 sanitizer the --agent surface enforces

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw agy run: IPD 9yd6tx executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-7tixnq-01-9yd6tx-give-the-json-surface-one-declared-leak-posture-and-sanitize.ipd.md); evidence .aw/records/plans/executed/20260930-7tixnq-01-9yd6tx-give-the-json-surface-one-declared-leak-posture-and-sanitize.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: 9yd6tx
- 2026-09-29 created (aw backlog): Carrier filed while authoring plan wqiofa (backlog un6ppd). Measured: a CommandResult carrying a home path in next_actions emits that path verbatim through JsonRenderer.emit, which returns normally and writes output, because JsonRenderer.render is a single json.dumps(result.to_dict()) call that never touches agent_schema. AgentRenderer, by contrast, routes through CommandResult.to_agent_record, whose _HOME_PATH_RE rule REFUSES the same value. So the two machine surfaces have different leak postures for identical input, and --json is the weaker one. This is NOT a crash, which is why it is excluded from wqiofa (that plan guards the raise at the agent serializer and leaves both other renderers untouched). The question is whether --json should adopt the same path normalization, which is a decision about what --json PROMISES: it is documented as 'full structured JSON representation', so a caller may legitimately want absolute paths, and silently rewriting them could break a consumer. Needs a maintainer's view on the intended posture before any code change.
