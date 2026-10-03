# Review findings: plan 1dkj1n

- Subject-Id: 1dkj1n
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `7bbb8557a` in an isolated, non-interactive review lane (no human interaction channel was
available to this turn). The plan was committed and byte-identical to the lane input, so no pre-review snapshot
was needed. `aw ipd lint --phase author --agent` was clean before semantic review. After revision,
`--phase review-finalize` reports `IPD-Q501` (error) on OQ-01, which is INTENDED: see PR-001. It also reports
`IPD-Z602` (info) on E-05's density, which is accepted below.

Reproduced in the lane, all matching the plan (`tmp/pr/oc.py`, `oc2.py`, `oc3.py`, gitignored):
`ON_CONFLICT_CHOICES` `('drop','refuse','force','prompt','ask')` vs `CANONICAL_ON_CONFLICT_CHOICES` (four);
both `oc_runipd.build_parser()` and `agy_runipd.build_parser()` return `ask` for `--on-conflict ask` and exit 2
for `maybe`; both hosts expose the identical eleven `on_conflict` option strings F-03 lists;
`resolve_on_conflict('ask')` -> `prompt`; `config.policy_on_conflict` carries `if val == "ask": val = "prompt"`
and the docstring "Normalizes 'ask' to 'prompt'" (`agent_workflows/config.py:1913`, `:1977`); spec fence
`[--on-conflict <drop|refuse|force|prompt>]` (spec line 201) and bullet (line 227); spec 5.3a "MUST be declared
in Section 2.1 in the SAME change" (line 1261); `start --help` renders `{drop,refuse,force,prompt,ask}`;
carriers `8wpjeq` (pending) and `woxgyo` resolve.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Executability / truthful blocking classification | OQ-01 `- Blocking: no`; E-02 "If the maintainer declines to decide ... STOP"; E-03..E-06 `Depends on: E-02`; the gate's "E-02 cannot be performed autonomously" | OQ-01 was marked non-blocking because "E-02 obtains the answer". An unattended `aw oc run` turn has no channel to ask, so the runner would dispatch an approved plan whose E-03..E-06 are unperformable, and the plan could never pass pre-transition. That spends a full turn for nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 set to `Blocking: yes`, with instructions to answer in the plan. E-02 now records and verifies a pre-answered OQ-01; V-02 and the gate were reconciled. The question itself remains OPEN for the maintainer. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing (non-vacuity) | `tmp/pr/oc2.py`: `after module-attr patch, parser accepts maybe: False`; `oc3.py`: row `._replace` patch -> parser accepts `maybe`, resolver raises `RunFlagRefusal` | V-05's perturbation ("temporarily adding a sixth accepted value") is ambiguous. The obvious tuple patch does not reach the parser because the `RunPolicyFlag` row captured the tuple at import, so the test would stay green. The invariant test also did not say where its accepted set comes from. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05: read the accepted set from the live parser. V-05: perturb the row, with the demonstrated route. |
| PR-003 | LOW | UNDER-SCOPE | D. Honest docs | `runner_shared.resolve_on_conflict` docstring "Choices: 'drop', 'refuse', 'force', 'prompt' (or 'ask')." | Under REMOVE, a second docstring still claims the alias. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 and V-04 now cover it. |
| PR-004 | LOW | IN-SCOPE | F. UX / spec accuracy | `start --help`: `[--conflict {drop,refuse,force,prompt,ask}]` vs zero-arg `--drop-running` etc. | E-03(b) would list six "alias spellings" without distinguishing the value-taking `--conflict` from zero-arg switches, which would misdescribe it to operators. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03(b) now requires the two kinds to be kept apart. |
| PR-005 | LOW | IN-SCOPE | G. Consistency | Proposed changes 1 "all nine findings" vs E-01/V-01 "F-01 through F-08" | Count mismatch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Wording reconciled. |

`IPD-Z602` (info) on E-05 is accepted. The item's bundled clauses are one test file plus one in-tree comment
about the same flag surface, which can be done in one focused pass. No split was made.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should OQ-01 block dispatch? | Yes. A maintainer answer is required in the plan before the runner can execute it. | Keep `Blocking: no` and rely on E-02's in-turn ask (unreachable unattended); split E-01 into its own plan (adds a plan for a measurement that review already reproduced) | The plan's own gate says E-02 "cannot be performed autonomously"; `IPD-Q501` is the shipped mechanism for exactly this | yes |
