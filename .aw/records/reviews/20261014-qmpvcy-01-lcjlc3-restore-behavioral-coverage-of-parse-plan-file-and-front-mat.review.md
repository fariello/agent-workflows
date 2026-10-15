# Review findings: plan lcjlc3

- Subject-Id: lcjlc3
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`d283c92f0`), so no snapshot was needed. `aw ipd lint --phase author` was clean before the review. After the review, `--phase review-finalize` is clean and `--phase pre-transition` reports only the expected unexecuted-state S404 items.

Evidence measured at review:

- The reader return values match the plan's Step-0 claims. The public readers return `abc123 approved` for all three spellings. The internal readers return the values for one space and `None None` for two-space and tab. Both return `None` for the multi-word status.
- `parse_plan_file` (`runner_shared.parse_plan_file`) binds the permissive public aliases and falls back to `plan_bucket(path)`. The docstring paragraph "THE ALIASES ARE THE PERMISSIVE PUBLIC READERS" contains "no live guard currently asserts this loose-whitespace tolerance".
- The four deleted tests in `19313eed^:tests/test_runner_refork_guard.py` `FrontMatterReaderBehaviorTests` match the plan's description.
- Mutation prototype, in a gitignored `.aw/state/` scratch copy (deleted afterwards), with only the `parse_plan_file` status import swapped to strict `_read_status`:
  - `python3 -m unittest` reported `FAILED (failures=4)`: the two-space and tab subtests on both hosts, `('abc123','pending','child') != ('abc123','approved','child')`;
  - the one-space subtests and the single-token prototype passed;
  - pytest from the lane root passed 2/2 under mutation because it imported the lane's own package, and pytest from the scratch root reported one FAILED with only the first subtest.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G. Lifecycle / durable carrier | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation: 4 obligation(s) name no durable carrier: deferred row 1..4` | None of the four Deferred rows carried a carrier field, so the plan could not finalize after execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to every row. Pre-transition now reports S404 only. |
| PR-002 | MEDIUM | IN-SCOPE | E. Non-vacuity feasibility | Review probe: a scratch-copy mutation passed 2/2 under pytest from the wrong root; pytest 8.2.2 without a subtests plugin reports one FAILED per `subTest` test and stops at the first failure; `runner_shared.py` has four other `from agent_workflows.selectors import _read_status` lines | As written, the "scratch" non-vacuity check could pass vacuously or show only one failing subtest, and a broad text substitution could hit the wrong import. The mutation was also not ordered before E-04's edit of the same file, so its `git checkout --` revert could discard the docstring change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The mutation is now made IN PLACE on the single `parse_plan_file` import, run with `python3 -m unittest -v`, ordered after E-03 and before E-04, and reverted with an empty `git diff --stat`. The measurement and pitfalls are recorded in Step 0. |
| PR-003 | LOW | UNDER-SCOPE | D. Anti-regression baseline | V-04 "summary line showing the full suite passing" | There was no pre-edit baseline, so the full-suite bar was absolute. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The baseline is recorded before E-01 (V-01), and V-04 compares failing-id sets. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract / precision | Gate "move the plan to `.aw/records/plans/executed/`"; OQ-01 `Owner: none`; E-01 `parse_plan_file(path, tmp)` (needs a `Path`); E-03 did not exclude a token leak | The gate lacked the honesty rule, a scope fence, conditional finalize ownership and never-tag. The owner was a placeholder, and two small precision gaps remained. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate. Set the owner to `plan author`. Changed the call to `Path(tmp)`. E-03 now also asserts the status is not `"EXECUTED"`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which runner should show the per-subtest non-vacuity failures? | `python3 -m unittest -v` | pytest (shows only the first failing subtest without a plugin); adding pytest-subtests (a new dependency) | Review probe output; pytest 8.2.2 installed | yes |
| D-2 | How to carry the four deferrals? | `Carrier-Declined` with reasons | New backlog items (no outstanding obligation: P16-forbidden pins and accurate history comments) | Backlog `qmpvcy` text "never a source-reading pin (P16)"; yuhl6o S-12 RETIRE-PIN | yes |
