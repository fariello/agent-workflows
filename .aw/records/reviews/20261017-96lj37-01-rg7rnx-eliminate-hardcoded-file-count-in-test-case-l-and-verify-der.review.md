# Review findings: plan rg7rnx

- Subject-Id: rg7rnx
- Subject-Type: ipd
- Reviewed-At: 2026-10-18
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `a84e38df4`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `test_case_l_tracked_install_still_writes_target` carries assertions (a)-(e) and no literal count or
  xfail; last change to the file is `baf8f38c0` (`work(3nczai)`), which removed the xfail.
- `84cba788c` removed `self.assertIn("358 files changed", tail)`; `9ca816dba` added `357`; `a75488af5`
  bumped to `358` (plan F1/F2/F3 correct).
- `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -k test_case_l -v`:
  `PASSED`, `1 passed, 22 deselected`. Module under `-n 6`: `23 passed`.
- Plan `3nczai` is in `executed/` with the identical E-01/E-02 and recorded mutation failures.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric G (context / redundancy) | `.aw/records/plans/executed/20261017-6i9viq-01-3nczai-...ipd.md` E-01/E-02 `Execution state: performed`; `git log -- tests/test_clean_target_config_home.py` tip `baf8f38c0` | The plan did not say that the identical verification already executed under `3nczai`, so a reader could not tell this is a re-confirmation whose real purpose is to carry `96lj37`'s release gate. | all Low | FIXED | Added F6 and a Deferred row naming the retire-instead alternative (D-1). |
| PR-002 | LOW | IN-SCOPE | Evidence accuracy | plan F4 "Commit `24e4c39cc` added `@pytest.mark.xfail`" | `24e4c39cc` is the integrate merge; the xfail was added by `e376b85ae` and removed by `baf8f38c0`. | all Low | FIXED | F4 cites both commits. |
| PR-003 | LOW | IN-SCOPE | Evidence accuracy | plan F5 "finds no numeric count assertions"; `tests/test_question_drain.py` `assert "20 files changed" in commit_stat` | The claim is false; one other literal exists, though it is fixture-controlled. | all Low | FIXED | F5 restated with the measured exception and why it is out of scope. |
| PR-004 | LOW | UNDER-SCOPE | Rubric E (mutation underspecified) | plan E-02 "e.g., cached removal of `AGENTS.md`" | Mutation insertion point, exact commands and revert command were left to the executor. | all Low | FIXED | E-02 gives the exact statements, insertion point, run command and `git checkout --` revert (the shape `3nczai` executed). |
| PR-005 | LOW | IN-SCOPE | Rubric E / live-artifact convention | plan V-01 "showing `1 passed`"; V-01 demands `git show 84cba788c` | A count bar and a historical diff (which predates the xfail removal) do not show the current method state; xfail/XPASS not excluded; no staged-set check. | all Low | FIXED | V-01 demands the current method text, `PASSED` (not XPASS), and a `files changed\|xfail` grep; V-02 adds `git diff --cached --name-only`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Retire this plan as superseded by `3nczai`, or keep it for execution? | Keep and execute | Retire to `superseded/` and close `96lj37` via `aw backlog set done 96lj37 --evidence <3nczai>` (SATISFIED route) | AGENTS.md close-legitimacy rule: either route preserves the `Blocks-Release: next` gate; execution is self-contained, cheap (~25s), and needs no lifecycle act outside a review | yes |
