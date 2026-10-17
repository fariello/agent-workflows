- Id: szjsgj
- Status: parked
- Set: rq
- Priority: low
- Work-Kind: feature
- Summary: Signal as an answer channel for runner questions (deferred by spec 6kwd2e R10.10): only via a user-run signal-cli daemon through the R10.8b command hook, or a dedicated adapter if Signal tooling becomes lighter

## Workflow history
- 2026-10-17 created (aw backlog): Signal as an answer channel for runner questions (deferred by spec 6kwd2e R10.10): only via a user-run signal-cli daemon through the R10.8b command hook, or a dedicated adapter if Signal tooling becomes lighter

Deferred by spec 6kwd2e R10.10 (amended 2026-10-17). All four bao493 responses (kdg4uz, cpcn9k, 49sv63, js5p5k) recommend not shipping Signal as a built-in channel: the only realistic route is signal-cli (Java 25, ~124 MB, releases may stop working after ~3 months), it needs a dedicated or linked number (linked devices unlink after ~45 days idle), it has no buttons, and automated use of a personal account risks ToS action. Revisit if (a) the R10.8b command hook proves insufficient for users who already run signal-cli, or (b) a maintained, lightweight Signal client appears. Do not start before the Telegram channel (Set qchan) ships.
