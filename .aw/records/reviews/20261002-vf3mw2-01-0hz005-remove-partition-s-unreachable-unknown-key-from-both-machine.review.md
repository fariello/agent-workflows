# Review findings: plan 0hz005

- Subject-Id: 0hz005
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `45529f342`. The plan was committed (`4180f3451`) and the
tree clean, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` reported clean
before semantic review and `--phase review-finalize --agent` reports clean after revision. The plan's
first `- Kind:` bullet reads `child`, so `IPD-S407` does not apply.

Re-measured and confirmed: `collect`'s sole return is `return candidates, []` (`agent_workflows/partition.py:463`)
and the other two returns in its range belong to `_is_runnable` (lines 326, 329); eleven `raise ValueError`
inside `collect` (13 module-wide); five `unknown` hits (372, 393, 528, 610, 621); live
`partition -t plans nosuchid99 --agent` exits 2 with a one-line stderr and no record; the live `--agent`
record ends `"unknown":[]`; `git tag --contains 309bc7909` is empty and the newest tag is `v1.3.0-rc.1`;
`tests/test_partition.py` has six unpacking `collect` call sites (346, 351, 357, 363, 377, 383) and two
inside `pytest.raises` (369, 373); the sole presence assertion is line 506; `test_cli_partition_agent_mode`
never reads `unknown`; no module outside `run_partition` imports `partition.collect`; `z7ci8k` E-05 says
do not delete the key; `python3 -m pytest tests/test_partition.py -o addopts=""` gives `22 passed`;
`python3 -m mypy agent_workflows` gives `Success: no issues found in 185 source files` on mypy 2.3.1.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E (verification feasibility) | plan V-05 dash check; probe on a file holding a real em dash and the text `u2013` | `grep -n '[\u2013\u2014]'` is a basic-grep bracket of literal characters, not code points: the probe missed the real em dash and matched the plain text `u2013`. The evidence demand would give false clears and false hits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 now demands `git diff -U0 CHANGELOG.md \| grep '^+[^+]' \| grep -P '[\x{2013}\x{2014}]'` printing nothing, demonstrated to match the em dash, and forbids the broken form. |
| PR-002 | MEDIUM | IN-SCOPE | G (execution contract) | plan gate paragraph "Execute through `aw ipd begin`..."; `agent_workflows/ipd_lifecycle.py:73` `EXECUTION_ROLE_ENV` | The gate unconditionally instructs the executor to run `aw ipd begin`/`finalize`; in a managed lane the runner owns both and refuses an agent (`AW-LIFECYCLE-ROLE-001`). The workflow names an unconditional finalize instruction as a finding. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten as conditional ownership: runner owns the transition in a managed lane, the hand executor runs begin/finalize otherwise, never a hand `git mv`. |
| PR-003 | MEDIUM | IN-SCOPE | E (evidence accuracy) | plan E-01 and V-01; `grep -n 'unknown' agent_workflows/partition.py` -> 372, 393, 528, 610, 621 | E-01/V-01 told the executor to classify the five grep hits as including a "producer", but the producer is the literal `[]` at line 463, which carries no `unknown` token. The five hits are two refusal messages, one binding, two emissions; an executor following the text literally could not satisfy it or would misreport. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both items now name the real classification and state that the producer is evidenced by reading `collect`, not by the grep. |
| PR-004 | LOW | IN-SCOPE | G (accuracy) | plan E-02 and Step 0 conventions; `agent_workflows/partition.py:34-38` `item_sort_key` | The `Tuple` use at line 38 is `item_sort_key`'s return annotation; no `_component_sort_key` exists in the module. The conclusion (keep the import) is right, the symbol is wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both mentions corrected to `item_sort_key`. |
| PR-005 | LOW | IN-SCOPE | G (live-artifact criteria) | plan V-04 "(authoring baseline: 22 passed)" | A collected test count is an artifact of test organization and may not be a V-item's bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 now demands zero failures/errors with 22 as context only; the bar is the pinned behaviors already enumerated. |
| PR-006 | LOW | IN-SCOPE | G (decision ownership); Scope check accuracy | plan OQ-01, OQ-02 `- Owner: none`; Scope check "four E-items" | Self-resolved questions should record the resolver as owner; the Scope check said four E-items while the plan has five. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owners set to `plan author`; Scope check reads five E-items (one measurement, four edits). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is removing a key from an `aw.agent/v1` payload a breaking change requiring a schema bump or maintainer sign-off? | No; removal proceeds as a plain `Changed` entry. | Mark BREAKING; bump to `aw.agent/v2`; keep the key. | `git tag --contains 309bc7909` empty (command never released); `docs/cli-output-contract.md` Section 8 governs released surfaces; no in-repo reader of the key (grep of agent_workflows, tests, tools). | yes |
| D-2 | Should this plan declare an `Item-Dependencies` edge with `z7ci8k`, which edits the same dict literal? | No edge. | Edge in either direction. | Edits are disjoint (`commands` value vs `unknown` entry); runner isolates each plan in its own worktree and merges through revalidation (AGENTS.md runner section). | yes |
