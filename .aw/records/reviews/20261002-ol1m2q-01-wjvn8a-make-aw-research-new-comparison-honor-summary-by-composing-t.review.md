# Review findings: plan wjvn8a

- Subject-Id: wjvn8a
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032752Z-4094028` at HEAD `ea6badb04`. The plan was
committed and byte-identical to the sealed lane input (rev-10, sha256 `029d8f49...`); no snapshot needed.
`- Kind: child`, so `IPD-S407` and `IPD-S408` do not apply. `aw ipd lint --phase author` clean before review;
`review-finalize` clean after.

Re-measured: `research_cmd.plan_new_comparison` still passes the three hardcoded role literals to `_mk`, whose
`build_frontmatter` call reads `summary=sm or summary` (F-02 holds). `deftzy` is `executed`; `plan_new_comparison`
now calls `_refuse_unsafe_descriptive` on `summary` (a newline value is refused; `"u"*290` and `"   "` pass), and that
helper imports `attention_contract` lazily, so no module-level `A` exists. `A.MAX_DESCRIPTIVE_LEN == 300`; a
290-char user value composed with the prompt role is 334 chars (F-07 holds). A fixture with
`records_backend: repository` reproduces the defect (four placeholder summaries, user string absent).
`python3 -m pytest tests/test_research_cmd_create.py` -> `16 passed`. `aw research index --check --agent` -> 179
findings (authoring: 142).

Side effect of review measurement: one bare `git init` fixture run (before PR-003 was understood) wrote four
research files under the HOME-scoped `~/.aw/projects/rv-wjvn8a-ab5244/`, outside the lane; the lane sandbox refused
their removal. They are untracked scratch output and should be deleted by a human.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G executability / stale premise | `.aw/records/plans/executed/20261001-7w6zsl-01-deftzy-...ipd.md:9` "- Status: executed"; `research_cmd._refuse_unsafe_descriptive` "from agent_workflows import attention_contract as _A" (lazy) | E-01 said `deftzy` adds a module-level `attention_contract as A` import that may already be present; it did not (lazy import inside the helper). F-08, OQ-04 and the gate described `deftzy` as `to-review` and the guard as absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now states the module-level import is absent and is added here, leaving the lazy one alone; F-08, OQ-04 and gate annotated as satisfied. |
| PR-002 | MEDIUM | IN-SCOPE | E testing | Required tests list `tests/test_research_contract.py`; `ls` -> "No such file or directory" | The targeted regression set named a nonexistent module and omitted `tests/test_research_descriptive_safety.py`, which guards the same `summary` input. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | List replaced with existing modules including the descriptive-safety tests. |
| PR-003 | MEDIUM | IN-SCOPE | E testing / reachability; B hygiene | bare `git init` fixture: `aw research new-comparison ... --apply` -> "wrote ~/.aw/projects/rv-wjvn8a-ab5244/records/research/..." | Without `records_backend: repository` a fixture writes outside itself, so F-01's "grep over the whole fixture returned nothing" proves nothing and V-02's demanded greps would find nothing even after a correct fix; it also leaves residue outside the workspace. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New Step 0 convention, Required tests and V-02 require the fixture to carry `.aw/config/project.json` = `{"records_backend": "repository"}` and to paste a `wrote` line inside the fixture. |
| PR-004 | LOW | IN-SCOPE | G live-artifact baseline | `aw research index --check --agent` -> `findings:179` vs authored 142 | V-04 compared against the authoring diagnostic population; it has drifted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 and Required tests now take a pre-change rule set at the executing HEAD; counts are context only. |
| PR-005 | LOW | IN-SCOPE | E falsification ordering | E-03 "Depends on: E-02" vs V-03 requiring a pre-E-02 RED run | The checklist order made the mandated pre-fix failure awkward to obtain. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now says write the test after E-01 and run it before E-02 (or in a worktree). |
| PR-006 | LOW | UNDER-SCOPE | Documentation sync | Spec/doc sync "owed at release, not from this plan"; `CHANGELOG.md` has 39 `- Fixed:` lines under `## 2.0.0 (pending)` added by fixing plans | A user-visible behavior change was deferred out of the changelog, against repository practice. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-05/V-05 and `CHANGELOG.md` to Scope-Paths, commit command and scope fence. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should this plan carry the CHANGELOG line? | Yes, as E-05 | leave to release-notes (contradicts the repo's per-plan `- Fixed:` practice) | `CHANGELOG.md` `## 2.0.0 (pending)` entries; executed plan `w89bo8` E-05 | yes |
| D-2 | Keep `- Item-Dependencies: executed:deftzy` now that it is satisfied? | Keep | remove (loses a true, free ordering record) | `deftzy` in `executed/` | yes |
| D-3 | Keep OQ-01's composition decision (made by the author on corpus evidence)? | Keep | prompt-only, bare replace | F-04/F-05; reversal confined to one helper | yes |
