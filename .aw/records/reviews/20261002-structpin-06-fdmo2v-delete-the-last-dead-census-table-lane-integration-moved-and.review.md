# Review findings: plan fdmo2v

- Subject-Id: fdmo2v
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `d5b97344f`. The plan was committed and byte-identical to the lane input, so no snapshot commit was needed. `aw ipd lint --phase author` and `--phase review-finalize` both report `clean`. `- Kind: child`, so `IPD-S407` does not apply.

The core claims reproduce:
- AST census: `{BOTH: 20, _MODULES: 25, INJECTED: 1, LANE_INTEGRATION_MOVED: 0, HOST_LABELS: 2}`.
- The dynamic-access grep returns nothing.
- `rg -n LANE_INTEGRATION_MOVED` gives 3 lines in the test file, and the test file is the only non-`.md` file that mentions it.
- `INTEGRATION_CAUSE_SHARED` and `test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners` have 0 hits in any `.py` file.
- `SUPERSEDED_SINCE_MOVE` is gone.
- Exactly two other pending plans declare the file: `qkwu1r` and `x3zno3`.
- `python3 -m pytest tests/test_runner_shared.py -o addopts=""` gives `135 passed`.
- The pinned hooks are ruff `v0.4.4`, with `ruff --fix` and `ruff-format`.
- The three suite-failure carriers are open backlog items.

I simulated the E-01 cut in memory, between the two content anchors. It removes 26 lines and leaves 0 mentions of `LANE_INTEGRATION_MOVED` and 0 of `LaneIntegrationExtractionTests`. The survivor census is unchanged, and `ruff check --select E4,E7,E9,F -` and `ruff format --check -` both exit 0. The widening argued in F-03 and F-04 is correct: the paragraph below the table is wholly dead.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G (deferral routing) | `x3zno3` Deferred row "they are not given E-items because neither concerns `should_color`" / `- Carrier: xvp5vx`; `xvp5vx` `- Status: done` with 0 mentions of `LaneIntegrationExtractionTests`; backlog `3tov52` open | The Deferred row named `x3zno3` as `- Carrier:` and cited it as `- Carrier-Evidence:`. F-07, Scope, Under-scope and OQ-01 all said `x3zno3` "routes"/"owns" the three production citations. In fact `x3zno3` EXCLUDES them and hands them to `xvp5vx`, which is done and never carried them. `x3zno3` also does not declare `oc_runipd.py`. So the remaining three dead citations were effectively stranded, and a `Carrier-Evidence` claim was false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The carrier is re-routed to open backlog `3tov52`, which owns the dangling test-symbol citation class. The three sites are named in the row as the handoff, because `3tov52`'s text does not yet name them and this plan may not edit it. The false `Carrier-Evidence` is removed. F-07, Scope, Under-scope and OQ-01 are corrected; OQ-01's owner changes from `none` to `plan author`. |
| PR-002 | LOW | IN-SCOPE | E | In-memory cut between anchors | Neither E-01 nor V-01 stated the expected removed-line count, so an overshoot or undershoot could only be judged by eye. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now expects 26 removed lines and 0 added, and records review's in-memory verification. V-01(e) requires `--numstat` showing `0 26`, or an explanation. |
| PR-003 | LOW | UNDER-SCOPE | E | `.pre-commit-config.yaml` `ruff-format` hook | Validation checked only `ruff check`, but the pinned hook also runs `ruff-format`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required tests item 6 and V-01(f) now also require `ruff format --check`. Review verified it passes on the cut. |
| PR-004 | LOW | IN-SCOPE | G (execution contract) | Gate "`aw ipd finalize` for the terminal transition" | The gate told the executor to run `aw ipd finalize` unconditionally, with no runner/executor split. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now says the runner finalizes under `aw oc run`/`aw agy run`, and a human-driven run uses `aw ipd finalize ... --actor ... --apply`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Which carrier owns the three surviving production-file `LaneIntegrationExtractionTests` citations? | Open backlog `3tov52`, with the sites named in this plan's Deferred row | (a) Keep `x3zno3`: rejected, it explicitly excludes the family. (b) File a new backlog item: rejected, it duplicates `3tov52`'s class and this plan cannot write outside Scope-Paths. (c) Widen this plan to the production files: rejected for the collision and scope reasons OQ-01 already gives. | `x3zno3` Deferred row; `xvp5vx` done with no mention; `3tov52` Summary | yes |
| D-2 | Is the widening beyond the backlog item's literal sentence acceptable? | Yes | Delete the table only: rejected, the in-memory check confirms it would leave 2 dangling mentions. | In-memory cut, plus a `.py`-wide 0-hit check of every symbol the paragraph cites | yes |
