- Id: 42da1n
- Status: open
- Blocks-Release: next
- Set: 42da1n
- Priority: low
- Work-Kind: bug
- Summary: emits_structured_tool_events is asserted from host identity and reads False for antigravity, which streams stream-json and is parsed

## Workflow history
- 2026-09-28 created (aw backlog): emits_structured_tool_events is asserted from host identity and reads False for antigravity, which streams stream-json and is parsed

MEASURED 2026-09-28 at HEAD e0717990 while authoring plan qul11h (backlog plsx3r), and reported rather than fixed because flipping this field CHANGES BEHAVIOR and so needs its own reviewed plan.

WHERE: agent_workflows/host_sandbox_profile.py, the `emits_structured_tool_events = True` assignment inside `detect_host_capabilities`'s `if host == "opencode":` branch.

WHAT IS WRONG. The field is asserted from HOST IDENTITY rather than from an executed probe, which is the exact anti-pattern this module's own docstring forbids ("WHY THE PROBE EXECUTES INSTEAD OF INSPECTING") and which review mjx7ne PR-007 already named ("contradicting the attempt-not-inspect discipline its own docstring publishes"). The verdict also looks WRONG for antigravity: agy_runipd.run_agy_turn passes `--output-format stream-json`, and agy_runipd parses those events (the `conversation_id` read plus the nested `result`/`init` lookup, and a per-step tool-event renderer). So `aw host capabilities antigravity` prints `NO emits_structured_tool_events` for a host that demonstrably emits and has its events consumed.

WHY THIS IS SEPARATE FROM plsx3r, which fixed the SIBLING field in the same branch. Unlike supports_session_resume, this field IS CONSUMED: `run_discovery_then_execution` refuses to claim a before-edit barrier unless `supports_read_only_phase AND emits_structured_tool_events`, and returns `barrier_enforced=False` otherwise. Flipping the value therefore changes a barrier decision rather than only a report, so it is a behavior change that needs its own plan, its own tests, and its own risk assessment. Plan qul11h's gate explicitly disclaims changing behavior, which is why it deleted only the session-resume half of that branch and filed this.

WHAT THE FIX LIKELY NEEDS, stated as a starting point and not a decision: an EXECUTED probe of each host's real event stream SHAPE (does a turn emit parseable structured tool events?), which is a different mechanism from reading one argv list. Note the honest hazard: `run_discovery_then_execution` today has no non-test caller, so a reviewer must decide whether flipping the field is a real behavior change or only a latent one, and say which.
