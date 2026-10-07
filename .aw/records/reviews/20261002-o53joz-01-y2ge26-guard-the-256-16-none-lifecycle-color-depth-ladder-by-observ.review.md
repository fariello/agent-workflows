# Review findings: plan y2ge26

- Subject-Id: y2ge26
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032752Z-4094028` at HEAD `da982415c`. The plan was
committed and byte-identical to the sealed lane input (rev-12); no snapshot needed. `- Kind: child`, so
`IPD-S407`/`IPD-S408` do not apply. `aw ipd lint --phase author` clean before review; `review-finalize` clean after.

Re-measured in-process with an isolated `XDG_CONFIG_HOME`: `term.COLOR_DEPTHS == ('none','16','256')`,
`len(ALL_STAGES) == 20`, `NATIVE_MAPS` 10 families / 83 words; all five seams exist with the cited signatures; at
pin `none` `lifecycle_depth()` is `'none'` and `style_lifecycle_text` returns bare `'blocked'` (fix live); at every
pin `status_256` returns `'\x1b[1;38;5;46mup to date\x1b[0m'` and `path` returns `'\x1b[38;5;33ma/b\x1b[0m'`
(F-08 holds). A 20x3x2x5 sweep with directly constructed `Resolved` values: 600 outputs, 0 failures, 0
`style_lifecycle_text`/`Palette.lifecycle` disagreements; M1 (monkeypatched `lifecycle_depth`) -> 40 red cells.
CLI on a synthesized 4-item backlog fixture with `PYTHONPATH` pinned (child imports the lane's package):
`find backlog --color` has 4 lifecycle spans at `256` and `16`, none at `none`, no escape at all at `none`;
`backlog check --color` has 0 lifecycle spans at every tier. No existing backlog item covers the generic axis.
No production file was modified (mutations were monkeypatches in a scratch process).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E testing / coverage | resolving every `NATIVE_MAPS` word reaches 17 of 20 stages; missing `integrating`, `none`, `reviewing` | E-03 says to enumerate stages from `ALL_STAGES` but does not say how to get a `Resolved` per stage; the natural route (resolve native words) silently skips three stages. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires constructing `Resolved(stage=s, style=STAGES[s], family=...)`; V-03 demands per-stage coverage including the three. |
| PR-002 | MEDIUM | IN-SCOPE | E testing / vacuity; C duplicate paths | `backlog check --color` 0 lifecycle spans at every tier; `tests/test_term.py::ColorDepthEndToEndLadderTests` already drives `find backlog --color` at three tiers | The anti-vacuity cell was stated per guard, not per command, so an added command with no lifecycle output would be a vacuous member. The plan also did not say how the new class relates to the existing end-to-end ladder test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04/V-04 require the anti-vacuity cell per command, name `backlog check` as a measured vacuous example, and leave the existing class unchanged with the new class's distinct value stated. |
| PR-003 | LOW | IN-SCOPE | G executability | `hasattr(term.Term, "resolve_lifecycle")` False; `term.resolve_lifecycle` exists at module level | E-01(a) could be read as calling a `Term` method that does not exist (it raised `AttributeError` during review). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now says it is a module function and there is no method. |
| PR-004 | LOW | IN-SCOPE | Honest classification / scope reconciliation | E-06 "file it as `followup`"; new backlog path not in `- Scope-Paths:` | Filing `followup` is itself a reading of OQ-02 (it keeps the item off the release gate), and the new record path needs a finalize justification. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06/V-06 mark `followup` provisional with the reclassify-to-`bug` path stated, and name the `--scope-reason` for a manual finalize. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep OQ-01 (reject the construction-level API change)? | Keep | adopt the API change | F-07: the coercion lived in a consumer; the guards are additive under either answer | yes |
| D-2 | Keep or replace `ColorDepthEndToEndLadderTests`? | Keep unchanged; new class is additive | merge into the new class (edits an existing test, against the plan's additive scope) | plan Scope check "no existing test is edited" | yes |
