- Id: an3vqw
- Status: graduated
- Graduated-To: specsread
- Blocks-Release: next
- Set: specsread
- Priority: medium
- Work-Kind: bug
- Summary: The --agent record omits the checked count at ZERO, hiding the exact case a validated-nothing verdict occurs

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set specsread (commit 2c7068ca).
- 2026-09-23 created (aw backlog): Found while executing IPD y4bdoz (specdirs Order 01); the plan deferred the fix and required it be reported.

MEASURED 2026-09-23 while executing IPD `y4bdoz`. `result_types.py` builds the count from `self.data.get('checked') or self.data.get('total_checked')`, and a falsy `0` fails that `or`, so the emitted `aw.agent/v1` record OMITS the `checked` key ENTIRELY when the count is zero. Observed side by side: a zero-spec repo emitted `{\"schema\":\"aw.agent/v1\",...,\"outcome\":\"clean\",\"exit\":0,...,\"findings\":0,...}` with no `checked` key, while this repository emitted `\"checked\":36`. The human branch prints no count at all, so `--json` is the ONLY surface that reports it.

WHY THIS IS A DEFECT AND NOT A COSMETIC GAP: the omission lands in exactly the dangerous case. A checker that examined ZERO artifacts and reported `clean` is the failure mode `y4bdoz` exists to prevent, and an agent consuming `--agent` cannot distinguish it from a genuinely clean tree, because the one field that would reveal it is absent precisely when it is zero. A test written against `--agent` to assert the count therefore passes VACUOUSLY, which is the same silent-success shape as the bug it would be trying to catch. `y4bdoz`'s own tests had to be routed to `--json` to avoid this.

SCOPE WARNING, which is why `y4bdoz` deferred it rather than fixing it in passing: that expression is shared by EVERY command emitting a count, so changing its falsy-`0` semantics is a cross-cutting output-contract change with its own blast radius (every consumer that currently sees no key would begin seeing `0`). It needs its own plan, an audit of the emitting commands, and contract-test coverage asserting `0` is emitted as `0` rather than dropped. The narrow fix is an explicit `is not None` test instead of `or`.
