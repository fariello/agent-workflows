- Id: 3f4ayi
- Status: open
- Blocks-Release: next
- Set: 3f4ayi
- Priority: medium
- Work-Kind: bug
- Summary: AgentRenderer.render_summary crashes whenever --fields is set

## Workflow history
- 2026-09-18 created (aw backlog): AgentRenderer.render_summary crashes whenever --fields is set

REPRODUCED 2026-09-18 while executing runanalytics Order 09 (ixis0c) E-01. Order 08 (mm5p3v) DOCUMENTED this defect in a code comment in `run_analytics_cli._emit_query_agent` and worked around it, but filed no backlog item, so it had no carrier a gate could see. This item is that carrier.

REPRODUCTION, exact:

    from agent_workflows.renderers import AgentRenderer
    from agent_workflows.result_types import OutputContext, OutputMode
    import io
    ctx = OutputContext(mode=OutputMode.AGENT, stdout=io.StringIO(), stderr=io.StringIO(), fields=['cmd'])
    AgentRenderer().render_summary('x', total=1, emitted=1, omitted=0, outcome='clean', exit_code=0, context=ctx)

    ValueError: Invalid aw.agent/v1 record: Summary record missing required field 'total';
      Summary record missing required field 'emitted'; Summary record missing required field 'omitted'

THE CAUSE IS TWO CONTRACTS THAT DISAGREE. `agent_schema.filter_record_fields` preserves only `_MANDATORY_FIELDS` (schema, kind, cmd, exit, outcome, verified, complete), while `agent_schema.validate_agent_record` ADDITIONALLY requires `total`, `emitted` and `omitted` on a summary record. So any caller that passes a `--fields` projection through to a summary raises instead of emitting.

WHY IT IS A BUG AND NOT A CHORE. It is a crash on a documented, user-reachable flag combination (`--agent --fields <...>` on any command whose answer is a bounded STREAM rather than one record), and the failure is a traceback rather than a refusal, so a caller cannot tell a malformed request from a broken tool. Per AGENTS.md, a live bug gates the next release, hence Blocks-Release.

IT IS CURRENTLY MASKED, NOT ABSENT. `run_analytics_cli._emit_query_agent` avoids it by rendering its summary WITHOUT the context, which is also the semantically correct choice there (projecting a summary's counts away would destroy the `emitted + omitted == total` invariant that distinguishes a bounded answer from a complete one). So no shipped caller hits it today, and the next stream-emitting caller that naively forwards `ctx` will.

SUGGESTED FIX, one of: (a) make `filter_record_fields` preserve the per-kind required fields, not just the shared mandatory ones, so a projection can never produce an invalid record; or (b) make `render_summary` ignore `context.fields` explicitly and document that a summary's counts are never projectable. (a) is the more general fix; (b) matches the semantics Order 08 reasoned its way to. Either way, add a test that renders a summary with `fields` set and asserts a VALID record rather than a raise.

NOT FIXED IN ixis0c: `renderers.py` and `agent_schema.py` are in neither Order 08's nor Order 09's Scope-Paths.
