# Review findings: plan l5f2hg

- Subject-Id: l5f2hg
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at `623eb73cb`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author` was clean; `--phase review-finalize` was clean after the revisions (one advisory `IPD-Z602` info).

Re-verified:
- `engine.agents_pointer_prose` contains the quoted sentence "When the user says \"use /askme\", \"/askme that question again\", \"ask that again using /askme\", or invokes `/aw askme`, read and apply `{workflows_dir}/askme/askme.md`".
- `engine.agents_managed_block(target_layout="aw").strip() in AGENTS.md` is `True` today, so the E-03 regeneration recipe starts from a synced block.
- `askme.md` has `## Recognize the request` (four-scope list) and `## Ask and wait` ("If the user says they do not understand, rewrite the question from scratch"); `rationale.md` uses dated-incident sections and carries no id6 handles.
- `tests/test_askme_command_delivery.py` has `test_agents_pointer_prose_names_askme` and the `slow` `test_installer_delivers_and_preserves_askme_shims`, which drives `engine.install_into_repo` with `SOURCE_WORKFLOWS` (`.aw/system/workflows`).
- `auwidn` Claude Code T01 quotes the two replies, the self-invoked `Skill {"skill": "askme", ...}`, and T02's typed slash command rewrite; D-10 maps to `l5f2hg`.
- `GEMINI.md` has no managed block; `CLAUDE.md` is absent, so `AGENTS.md` is the only derived copy to regenerate.
- No spec governs the pointer sentence (grep of `.aw/records/specs` for the phrase and for `agents_pointer_prose` shows only unrelated sections).
- F-2 cites a gitignored capture (`claude-01.jsonl`) that is not present in this lane and is not quoted in `auwidn`; not re-verifiable here.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Acceptance validity | `auwidn` `## Method` "history-free single-commit beds without this plan, its review, research `y0vcm9` or backlog `jymlaw`"; old E-05 "a disposable bed built from this branch" | The acceptance re-run would use a bed containing this plan, which states the expected behavior, so the trial agent could read the answer key (the test-validity failure `auwidn` already measured on two hosts). The `m4rcyy` fixture was never committed and the old E-05 did not say how to recreate it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now requires a history-free bed outside `.aw/worktrees/` with this plan, its review, `lkn1zt`, `auwidn`, `y0vcm9`, `jymlaw` removed; recreates `m4rcyy` verbatim from `auwidn` `### Trial bed (E-03)`. |
| PR-002 | MEDIUM | UNDER-SCOPE | E. Coverage of both failure paths | `auwidn` Claude Code T01 "first as a custom answer in the question tool, then as a free-typed chat message"; old E-05 "and if needed again in chat" | One session where the second reply may rescue the first would not prove the custom-answer path, which failed independently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Two fresh sessions, (a) custom answer and (b) typed in chat, each judged; named capture files; F-2 re-established from the new captures; stop condition on failure. |
| PR-003 | MEDIUM | IN-SCOPE | D. Target neutrality / installed bundle | `tests/test_agents_block_target_neutral.py` `test_fresh_install_managed_block_contains_no_aw_only_tokens`; old E-02 "citing `lkn1zt` `auwidn`" in `rationale.md` | The pointer ships to every managed repo and `rationale.md` ships in the installed bundle; citing local id6 handles there would dangle in targets, and E-01 did not restate the AW-only token constraint `er11a0` E-04 carried. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 states the target-neutral constraint; E-02 describes the incident by date in the existing style, naming research `auwidn` as source only; V-04 runs the target-neutral test explicitly. |
| PR-004 | LOW | IN-SCOPE | E. Test precision / P16 | old E-04 "the INSTALLED `askme.md`" (ambiguous: shim `.claude/commands/askme.md` vs body) | The installed shim never contains the body paragraph, so the assertion target was ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names `<target>/.aw/system/workflows/askme/askme.md`, the existing installer test or a sibling, output-only assertions (no source reads), and the CHANGELOG location. |
| PR-005 | LOW | UNDER-SCOPE | E. Evidence feasibility | old V-04 "(and failing against the pre-change code)" | Demanded contrast with no stated way to produce it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 names the mechanism (stash only the two changed paths, run, restore) and demands both outputs. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | old gate | Gate lacked an OQ status line, scope-fence declaration, the paste-actual-output honesty rule, the runner/hand finalize ownership split and the no-`git mv` rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all elements. |
| PR-007 | LOW | IN-SCOPE | G. Right-sizing | old E-05 bundled the suite run and the attended trial | Two independent concerns with different preconditions (one unattended, one needs the maintainer); also the `slow` target-neutral and installer tests run only in the thorough tier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-05 (bare suite plus `make test-all`) and E-06 (attended trials), with V-05/V-06. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the acceptance re-run also cover the three combinations that passed T01? | No; recorded as a deferral with reason | Re-run all four (more maintainer time for text those hosts already applied) | `auwidn` T01 row: pass on OpenCode + opus, OpenCode + gem, Antigravity; E-04 tests cover delivery on every host | yes |
| D-2 | Is a spec edit needed? | No | Amend a spec | No spec governs the pointer sentence; `er11a0` changed it without one | yes |
| D-3 | Must the trial bed be history-free? | Yes | Plain worktree of this branch (lets the agent read the expected behavior) | `auwidn` `## Method` isolation deviations | yes |
