# Review findings: plan fz3i3m

- Subject-Id: fz3i3m
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `19cc3d73d`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize` both reported `clean`. `- Kind: child`.

Reproduced every authoring claim at this HEAD:
- Census: `aw check specs --source-anchors` printed only `agent_workflows/check_engine.py:391: spec pqsx96 :135 -> ## 3. Invariant catalog`, exit 0. The pqsx96 spec line 135 begins `| I-07 | Release-gate preservation`.
- Crash: `aw check --source-anchors --agent` ended in `ValueError: Invalid aw.agent/v1 record: Exit code mismatch: exit=0 incompatible with negative outcome 'findings'`, rc 1. Cause: `cli._run_check` `--source-anchors` branch hardcodes `exit_code = 0` beside `status = "findings"`. `agent_schema` lists `conforms` in `POSITIVE_OUTCOMES`. The other check branch uses `core.drift_exit_code` and `"conforms" if exit_code == 0`.
- Supplementary grep: the three runner anchors and the test docstring.
- 25kzda: `### 1.1 Normative roles` sits at 128 and `### 2.1 Command grammar` at 185. "The frozen value cannot change on resume." is in the `--retry-budget` bullet, and the `--resume` mutual-exclusion sentence is at 221. Both are inside Section 2.1, so E-05's retarget is correct.
- Rule: `check.spec-anchor-stale` is `info` in `check_engine.RULE_REGISTRY`.

I prototyped E-04 in a scratch copy (`.aw/state/`, untracked) and ran it on the real tree. Without one-line docstrings it reported exactly the three runner anchors plus the pqsx96 row. It did not report the `runner_shared.py` `:16624` self-citation.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | A/E (detector completeness) | `agent_workflows/spec_citations.py` `stale_spec_anchors` one-line docstring branch (`if q in rest:` ... `continue`); review prototype with that branch covered additionally reported `tests/test_spec_citation_anchors.py 124 ? 131 unattributed` | E-04 did not say the unattributed rule must cover the one-line docstring branch, which `continue`s before the general path. An implementation that skipped it would leave a blind spot of exactly the class this plan exists to close. The plan's E-05 reword of that test docstring was presented as hygiene, but it is required for a zero census. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires the rule on the one-line branch and records both prototype censuses as context. E-05 states that the reword is required. |
| PR-002 | MEDIUM | IN-SCOPE | A/E (crash fix completeness) | `agent_workflows/cli.py` `--source-anchors` branch: both `Evidence(..., status="clean" if len(findings) == 0 else "findings")` | E-02 fixed the result status but left the two `Evidence.status` values computing `findings` beside exit 0. Zero-finding behavior was also unspecified. The `g3ropl` regression test (e) asserted only on the "first JSON record", with no zero-finding counterpart. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 derives the evidence statuses from the same exit code and keeps `clean` for zero findings. E-06 (e) parses every line and asserts the result record; added (f) for zero findings. V-02 and V-06 are updated to match. |
| PR-003 | LOW | IN-SCOPE | G (lifecycle) | `agent_workflows/runner_shared.py` `process_backlog_close` reads `item.get("from_backlog")` only; this plan's `From-Backlog` is `1vd74h`, and `l85xvi` is a second carrier | The gate's backlog instructions did not say which item the runner closes. `1vd74h` must stay `graduated`, and `g3ropl` (`Blocks-Release: next`) is closed by nobody unless done by hand, as a commit outside Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now states both facts and the `--evidence` SATISFIED close for `g3ropl` as a separate commit. |
| PR-004 | LOW | IN-SCOPE | G (execution contract) | Gate "carries no `- Readiness:` field" sentence; OQ-01 `Owner: none`; V-06 command ran under default addopts | The sentence went stale at review. The OQ owner was not recorded. V-06 could not show tests (a) through (f) by name. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed the sentence, added the honesty rule, made the finalize command concrete, set `Owner: plan author`, and changed V-06 to `-o addopts="" -v`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Must the unattributed rule cover one-line docstrings? | Yes. | Leave the one-line branch uncovered (keeps a blind spot; census would read zero while a stale anchor sat in a one-line docstring). | Review prototype run on both shapes; plan Goal ("zero because the tree is clean rather than because the detector cannot see"). | yes |
| D-2 | Which backlog item does the runner close, and who closes `g3ropl`? | Runner touches only `1vd74h` (stays `graduated`, second carrier pending); `g3ropl` is closed by hand with `--evidence` after execution. | Add `g3ropl` as this plan's `From-Backlog` (would drop the `1vd74h` link that `l85xvi` and the graduation rely on). | `runner_shared.process_backlog_close` reads `from_backlog`; AGENTS.md "Close-legitimacy rule" SATISFIED path. | yes |
