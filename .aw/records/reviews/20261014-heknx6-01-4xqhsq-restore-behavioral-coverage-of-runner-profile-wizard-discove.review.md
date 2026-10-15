# Review findings: plan 4xqhsq

- Subject-Id: 4xqhsq
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`a906e45cc`), so no snapshot was needed. `aw ipd lint --phase author` was clean before the semantic review, and `--phase review-finalize` was conforming after the revisions.

Verified at review with a scripted-IO probe against current code. The probe ran under the gitignored `.aw/state/` and was then deleted.

- **E-01 end to end.** The 7-answer script is fully consumed, with 1 write, `model == "example/private-model"`, and no numbered line before the manual prompt.
- **Bounded manual entry.** `select_model` raises `WizardCancelled` after exactly `MAX_ATTEMPTS` (5) prompts.
- **Exhausted `run_wizard`.** It returns `saved=False`, `cancelled=True`, `reason="cancelled"`, with 0 writes.
- **Invalid-then-valid entry.** It returns `example/ok` and emits both the "required" message and the "invalid model" refusal.
- **`m` from a live catalog.** It reaches manual entry.
- **Config fallback.** The emitted text names `timeout` and the count `2`.

Other checks:
- `git cat-file -t 19313eed7^` is `commit`, and the cited `_Script`, `_Store` and two tests exist there.
- `tests/test_cli.py` is the only test importing the module (`test_wizard_failure_is_reported_not_raised`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Verification (mutation sensitivity) | `runner_profile_wizard._report_catalog` final branch emits `catalog.reason` and `catalog.detail` in the same line; plan E-01 `detail="d-R"` | The authored fixture embeds the reason string inside the detail. The V-01 mutation (drop `catalog.reason`) would therefore still leave `R` on screen, so the test passes under the mutation and the mutation check cannot fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now uses `detail=f"detail-{i}"` and states that the detail must not contain the reason. The mutation is described as keeping the detail. |
| PR-002 | LOW | IN-SCOPE | E. Verification (revert ordering) | V-01 "`git diff --stat` ... proving only the E-03 docstring change remains"; Required tests mutation steps | The mutations edit the same file that E-03 later edits, and the plan never said to revert before E-03. V-01 therefore demanded a diff state ("only E-03 remains") that cannot hold at E-01 time. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both mutations now revert with `git checkout --` before E-03, and V-01 and V-02 demand an empty diff after the revert. |
| PR-003 | LOW | IN-SCOPE | A. Test precision | `select_variant` emits `"  [1] Provider default"`; E-01 "no `[1]` before the manual prompt" | "Before the manual prompt" needs an ordered record of asks and emits. A whole-text check would hit the variant menu's `[1]`. The 7-answer script was also unexplained. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires one ordered event list and an exhausted-script assertion, and explains why there are seven answers. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; `- Scope-Paths:`; OQ-01 `Owner: none` | The gate lacked a scope fence, the honesty rule, `aw ipd begin`, conditional finalize ownership, a never-tag rule, and a no-commit-of-mutation rule. Scope-Paths omitted the plan file. OQ-01 `Owner: none` passes lint as non-empty but is not a real owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The full contract is added, the plan path is added to Scope-Paths, and the owner is set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Accept OQ-01 (new purpose-named module)? | Yes, as authored | Re-create `tests/test_runner_profile_wizard.py` (would imply all five behaviors are guarded) | Module docstring "no live guard currently asserts these five behaviors"; sibling plans `55kl2u`, `yfo6z6` | yes |
| D-2 | Fix the mutation sensitivity by changing the fixture or by asserting the reason in a specific substring? | Change the fixture so the detail is reason-free | Assert on `f"({R}"` (couples the test to punctuation) | `runner_profile_wizard._report_catalog` output format | yes |
