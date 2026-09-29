- Id: 1urnej
- Status: open
- Set: sevreg
- Priority: low
- Work-Kind: chore
- Summary: five live drift rules are absent from RULE_REGISTRY and silently default to error severity

## Workflow history
- 2026-09-29 created (aw backlog): Carrier for an obligation deferred by plan nwcf8j (sevtruth), which declined to register them because changing a severity moves exit codes.

`check_engine.rule_spec` falls back to a default `RuleSpec` at `error` severity for any rule id absent from `RULE_REGISTRY`. That fallback is deliberate and conservative (an unregistered rule fails loudly rather than passing quietly), but it means an unregistered rule's severity is an ACCIDENT of the fallback rather than a recorded decision.

MEASURED at commit `39fdc610`: `RULE_REGISTRY` holds 52 rules, and these five live rules emitted by real code paths are NOT among them, so each resolves to `error` by fallback:

- `adopted-without-consumer` (35 findings on this tree)
- `stale-state-to-promote` (17)
- `dangling-citation` (11)
- `attention.lane-stranded`
- `attention.lane-superseded`

The last one is the clearest case that the fallback is not always right: `attention.lane_drift_severity` deliberately grades a superseded lane `info` so it reports without failing the gate, and that intent lives in a function rather than in the registry every other rule is described by.

WHY THIS IS NOT A BUG AND WAS DEFERRED: `artifact_core.drift_exit_code` exempts exactly `info`, so REGISTERING any of these at a non-error severity CHANGES EXIT CODES. That makes it a gating change wearing a reporting change's clothes, which is why plan `nwcf8j` (which only made existing severities visible) declined it. No user-visible misreport is claimed here, hence `chore`.

FIX SKETCH: register each rule explicitly with a recorded severity, assurance class and determinism, deciding each severity on its merits and stating the exit-code consequence per rule. Expect this to need review, since at least one (`attention.lane-superseded`) should arguably be `info` and that would flip a currently-failing gate to passing.
