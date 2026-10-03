# Review findings: plan aqyh40

- Subject-Id: aqyh40
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Structural preflight `aw ipd lint --phase author --agent` was clean before revision, and `--phase review-finalize --agent` is clean after. The plan was committed and unmodified (`44ad093ca`), so no pre-review snapshot was needed. No production file was modified. Every check was run in PREVIEW mode at review, and `git status --porcelain` hashed identically before and after.

Reproduced at review: `aw rename plans <filename> --slug zzz`, `aw group plans <filename> --set zzscratch` and `aw archive plans <filename>` each exit 0 and preview; `aw archive plans nonexistent-token-xyz` exits 2; a bare `aw archive plans` exits 0; `aw rename plans <a spec path>` exits 2 with `plans verb cannot act on ... it is not inside the plans records tree`; all six of `specs`/`prompts`/`backlog`/`walkthroughs`/`roadmaps`/`releases` refuse a plan path with exit 2; `aw archive plans researchorg` exits 0 and previews that Set; `check_engine._identity_rename_hint('roadmaps','7ny1bg','Id',False,path=...)` returns `aw rename roadmaps 7ny1bg --to-id6 --apply`, and that command exits 0. The comma-separated multi-edge `- Item-Dependencies:` form is used by existing plans. The authored design is sound. What was missing was coverage of the parent's completion criteria and a mutation check that works in a shared checkout.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G executability / coverage | `95jk4s` `## Completion criteria` items 2, 3, 4, 5, 6 | The child claimed to own the parent's whole-Set verification but covered only criterion 1, the spec-path refusal, and criterion 7. Criteria 2 (six generic types refuse), 3 (id6 from the declared `- Id:`), 4 (bare sweep exits 0), 5 (terse setid with parenthetical) and 6 (rename hint resolves) were not checked at the combined end state. The runner skips the parent's checkpoint, so that coverage gap is the same gap this child exists to close. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-06/V-06 (criterion 2), E-07/V-07 (criterion 5, setid re-derived at execution), E-08/V-08 (criterion 6); extended E-02/V-02 (criterion 3) and E-03/V-03 (criterion 4). |
| PR-002 | MEDIUM | IN-SCOPE | E verification | AGENTS.md "Shared checkout: you are not alone in this repo" | V-02/V-03 demanded unchanged whole-tree `git status --porcelain` before and after. In this shared checkout co-workers change the tree concurrently, so a correct execution could fail that check, or a failure could be hidden. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with per-target evidence: `ls <target>` still exists plus `git diff --stat -- <target>` empty; Required tests section reworded to match. |
| PR-003 | LOW | IN-SCOPE | G execution contract | plan `## Approval and execution gate` | The gate lacked the hard-MUST "paste the actual runner output" rule and conditional finalize ownership (runner in a managed lane, executor by hand), and its "stop" wording did not separate an unsafe condition from a scope question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all execution-contract elements; out-of-scope edits are justified at finalize, not a stop. |
| PR-004 | LOW | IN-SCOPE | G consistency | plan `## Proposed changes` | The proposed-changes list did not reflect the new E-06/E-07/E-08. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Swept and reconciled. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should the child re-verify every parent completion criterion or only the parent's literal "end-state consistency check"? | All criteria 1 to 7 | Only the literal check plus suite (as authored) | `95jk4s` `## Completion criteria` is a whole-Set obligation the runner never verifies on the parent | yes |
| D-2 | How to prove preview runs mutated nothing in a shared checkout? | Per-target `ls` plus `git diff --stat -- <path>` | Whole-tree `git status --porcelain` | AGENTS.md shared-checkout section | yes |
