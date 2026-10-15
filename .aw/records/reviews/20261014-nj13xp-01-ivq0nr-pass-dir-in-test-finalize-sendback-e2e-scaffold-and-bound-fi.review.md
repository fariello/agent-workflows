# Review findings: plan ivq0nr

- Subject-Id: ivq0nr
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

This review ran in an isolated, non-interactive review lane, so no human channel was available. The plan was committed and unchanged (`24401dfcd`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before the semantic review. After the revisions, `--phase review-finalize` reports exactly one error, the expected `IPD-Q501` on the escalated OQ-01.

Re-verified at review HEAD:
- `ipd scaffold --help` lists no `--dir`, while `ipd begin --help` and `ipd finalize --help` both list it (F-2 holds).
- `ipd_authoring.run_scaffold` calls `find_project_root(Path.cwd())` at three sites: `_setid_length_guard` (`:424`), the `--from-backlog` lookup (`:494`), and the derived destination (`:563`). The destination is composed as `repo_root / ".aw" / "records" / "plans" / _rp.target_subdir("plans", "to-review")`, and `artifact_core.atomic_write` does `path.parent.mkdir(parents=True, ...)`, which is how a stray `pending/` tree gets created.
- `tests/test_finalize_sendback.py` `test_e2e_real_finalize_checkbox_mismatch_is_retryable` runs scaffold, begin, and finalize with `cwd=repo_dir` and no `--dir` (F-1 holds).
- `project_context.find_project_root` is git-blind. That is a DECIDED and documented rule:
  - `no_project_message` docstring: "PROBING FOR GIT HERE IS A MESSAGE CONCERN AND MUST NEVER BE PROMOTED INTO `find_project_root` (`quqyc4` E-02). Root detection is DELIBERATELY git-blind"
  - `classify_project_dir`: "Git-blind"
  - executed `awretrofit-06` OQ-01
  - `quqyc4` E-02 deferral: "a decided question ... not an outstanding obligation"
- `doctor.run` bounds its own climb at the git root (`sjsb04` E-02), as F-3 says.
- Probe: an in-memory copy of the proposed bounded loop. In a nested uninstalled git repo under an outer `.aw/` it returns `None` (today it returns the outer project). From a subdirectory of a git-backed project and from a subdirectory of a non-git project it returns that project. From this lane worktree, where `.git` is a gitfile, it returns the lane itself.
- `resolve_verb_repo_root` falls back to CWD, not to the git root, when `find_project_root` is `None`.
- `/tmp/.aw` is absent on this machine at review, so the leak is not currently present here.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D. Domain invariants / project rule | `agent_workflows/project_context.py:449-453` (`no_project_message` docstring "MUST NEVER BE PROMOTED INTO `find_project_root`"); `classify_project_dir` "Git-blind"; `.aw/records/plans/executed/20260817-awretrofit-06-uh295u-cwd-climb-project-root.ipd.md` OQ-01; `quqyc4` E-02 | E-04 reverses a decided, documented rule: root discovery is git-blind. OQ-01 claimed it was "resolved from repository evidence" without citing the rule it overturns, and it even cited awretrofit OQ-01 as consistent. The change alters project discovery for every `resolve_verb_repo_root` caller (66 call expressions) and for `runner_shared`'s analytics probe. Any user in a nested uninstalled git repo (vendored clone, submodule, scratch clone) silently loses the outer project. This is a public-contract decision for the maintainer. E-01..E-03 already fix the reported leak without it. | C:Low; U:Medium-High; S:Low; F:Medium-High; Overall:Medium-High | OPEN | Reopened OQ-01 as `Blocking: yes`, `Owner: maintainer`, `Finding: PR-001`, with both options and the measured probe. E-04 is now gated on the answer, with a defined `blocked` path for option (b). |
| PR-002 | MEDIUM | UNDER-SCOPE | Documentation sync | the same three docstrings | If E-04 lands, three docstrings (`find_project_root`, `no_project_message`, `classify_project_dir`) would state the opposite of the code. The plan said "N/A". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now rewrites all three in the same edit, and V-04 demands them. The Spec/doc sync section was updated. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Verification / regression | backlog `nj13xp` body (the leak under TMPDIR) | No V-item reproduced the reported defect. Every evidence demand was a diff or a narrowed test pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06, V-03, and V-06 now require running `test_finalize_sendback.py` with TMPDIR under a scratch AW project and showing zero leaked plans. V-02 now requires a behavioral `--dir` proof, and V-01 a pre-change exit-2 contrast. |
| PR-004 | LOW | IN-SCOPE | G. Executability | `ipd_authoring.run_scaffold` derived-destination block | E-02 introduced a second path mechanism (`resolve_record_path` with a fallback) where the code composes the path directly. It also did not say that resolution must precede the setid guard, which runs first. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now says to substitute `repo_root` into the existing composition and to resolve it before `_setid_length_guard`. |
| PR-005 | LOW | IN-SCOPE | Test accuracy | `project_context.resolve_verb_repo_root` (`root if root is not None else Path.cwd()`) | E-05(2) implied that scaffold from inside a nested repo lands at the inner git root. That holds only from the repo root; from a subdirectory the fallback is cwd. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now says to run from the inner repo root and not to claim the subdirectory case. |
| PR-006 | LOW | UNDER-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate had no honesty rule, scope-fence declaration, commit path or never-push rule, ban on hand `git mv`, release-gate note, or Blocks-Release inheritance statement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten (no STOP clause). |
| PR-007 | LOW | UNDER-SCOPE | Documentation | `CHANGELOG.md` | A user-visible `--dir` flag on `aw ipd scaffold` (and possibly a change in discovery behavior) had no CHANGELOG entry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-07/V-07 and added `CHANGELOG.md` to Scope-Paths. Highest E is now 07. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can the reviewer settle whether discovery stops at an enclosing `.git`? | No. Escalated as blocking OQ-01 to the maintainer. | Accepting the author's resolution; descoping E-04 by reviewer authority, which is itself option (b). | AGENTS.md: ask the human for public contracts; the documented git-blind rule at `project_context.py:449-453` | no (escalated: OQ-01 `Blocking: yes`) |
| D-2 | Do E-01..E-03 fix the reported leak independently of E-04? | Yes. | Treating E-04 as required for the fix. | `resolve_verb_repo_root` honors an explicit `--dir` verbatim, and begin/finalize already accept `--dir` | yes |
| D-3 | In E-02, which path mechanism should the derived destination use? | Substitute into the existing composition. | `resolve_record_path` with a fallback, as the plan proposed. | `ipd_authoring.run_scaffold` derived-destination block; one-mechanism convention | yes |
