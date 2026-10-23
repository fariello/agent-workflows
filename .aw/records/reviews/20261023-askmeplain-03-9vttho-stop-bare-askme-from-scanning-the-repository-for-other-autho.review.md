# Review findings: plan 9vttho

- Subject-Id: 9vttho
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `623eb73cb`. The plan was committed and byte-identical to
the sealed lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`, 0
findings; after revisions `--phase review-finalize --agent`: `clean`, 1 `info` (`IPD-Z602`, E-01 may
bundle concerns). Z602 was evaluated semantically: E-01 is one concern (the item 4 rule plus its
one-paragraph rationale mirror, the same shape siblings `lf4j52`/`wfy9ii` use), so it was not split.
Not an orchestrator.

Verified at review:
- Installer delivery: a scratch `engine.install_into_repo` into a `tests.support.init_repo` temp repo
  produced `.aw/system/workflows/askme/askme.md` containing "Do not scan the entire repository" and a
  sibling `rationale.md` (`True True` / `True`), so the E-02 assertion target exists.
- `python3 -m pytest -o addopts="" -q tests/test_askme_command_delivery.py`: `3 passed in 5.60s`;
  `python3 -m pytest --co` collects 0 tests from this file (core tier), and
  `tests/slow_allowlist.txt` line 22 lists the installer sibling as slow.
- T05 evidence in findings `auwidn` (verdict matrix row "T05 no arguments, nothing outstanding |
  pass | FAIL | FAIL | FAIL", defect D-8) matches the plan's Concern verbatim.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric E (validation reaches the test) | `tests/test_askme_command_delivery.py:88` `@pytest.mark.slow` on `test_installer_delivers_and_preserves_askme_shims`; `pyproject` addopts `-m 'not slow and not livecorpus'`; review `--co` shows 0 tests from the file in the bare run | E-04/V-04 relied on bare `python3 -m pytest` and "the new test by path" without clearing the marker filter; an installer test belongs in the slow tier, so the bare run would never execute it and the plan gave no marker guidance. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 marks the test `slow`; E-04/V-04 run it with `-o addopts=""` and state the bare run is a regression gate only. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric D (internal contradiction) | `.aw/system/workflows/askme/askme.md:29-31` "confirm authorship before treating a record or question as yours (`git log` and the record's `- Author:` line settle it)" | Item 4 itself tells the agent to run `git log` to establish authorship, while the plan's new (b) forbids `git log --all` searches and (a) says to establish the session's records from the conversation. Leaving the sentence would keep a scan instruction inside the rule that forbids scanning. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 (e) replaces that sentence in item 4 and keeps the separate shared-checkout paragraph in `## Establish facts before asking` for item 3 records; E-02 asserts the sentence is gone from item 4. |
| PR-003 | MEDIUM | UNDER-SCOPE | Rubric D (preserve intended behavior) | `askme.md:20-25` items 2 and 3; plan E-01 (c) lists "an explicit request to scan" as a valid pointer | The prohibition was not limited to the no-argument case, so an executor could word it so broadly that an explicit scan request or item 3 record review is also refused. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 (e) scopes the limits to the no-argument case; invariants I-1/I-2 added and mapped to V-01. |
| PR-004 | MEDIUM | IN-SCOPE | Shared-checkout safety | AGENTS.md "Shared checkout": never stash or discard another party's work; plan V-02 "e.g. `git stash` of only `askme.md`" | V-02 suggested `git stash` to produce the pre-change failure, which in a shared checkout can sweep a co-worker's change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now gives a copy, `git show HEAD:` restore, and `git diff --stat` proof that the edit is back. |
| PR-005 | LOW | IN-SCOPE | Accuracy | `.opencode/commands/askme.md` body "Read and execute @.aw/system/workflows/askme/askme.md."; `engine.shim_body` | Scope said the test asserts "the generated shims ... carry the rule"; shims only point at the body, so that claim was false. CHANGELOG target and prefix were also unnamed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope corrected; E-03 names `## 2.0.0 (pending)` and the `- Fixed: ` prefix; Scope check records that the shim argument text and index row already match. |
| PR-006 | LOW | UNDER-SCOPE | Rubric G (execution contract, honest limits) | plan "Approval and execution gate"; research `y0vcm9` "Automated checks can establish that instructions were generated and delivered." | The gate lacked the paste-actual-output rule, the declaration-only scope fence and the conditional finalize ownership; the plan did not state that a delivery test cannot prove agents obey the rule, which T05 showed is the real failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with the full contract; Required tests gains the honest limit and the invariant map. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the new installer test be core tier or slow tier? | `@pytest.mark.slow`, run by path with `-o addopts=""` | Core tier (adds about 5 s to a gate budgeted under 30 s); rendering only, without an install (would not test the delivered file) | `tests/slow_allowlist.txt:22` lists the installer sibling; AGENTS.md repo-local suite contract (core tier budget); review timing `3 passed in 5.60s` | yes |
| D-2 | Keep or replace item 4's `git log` authorship sentence? | Replace it in item 4; keep the `## Establish facts before asking` shared-checkout paragraph | Keep both (contradicts (b)); delete both (loses the item 3 authorship check) | `askme.md:29-31` and `askme.md:64-67` | yes |
| D-3 | Should the deferred attended T05 re-run get a backlog carrier instead of `Carrier-Declined`? | Keep `Carrier-Declined` | File a backlog item | Siblings `lf4j52` and `pkz19w` decline the same re-run the same way; `.aw/records/plans/README.md` "Explicitly declined" leaves merit to the reviewer, and re-verification is the maintainer's discretionary act | yes |
