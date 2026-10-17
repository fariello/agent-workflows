# Review findings: plan im4afa

- Subject-Id: im4afa
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (HIGH, open), PR-002 (MEDIUM, open)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed (last touched by 84cba788c, which added its two `Carrier-Declined` lines); pre-review snapshot skipped. `aw ipd lint --phase author --agent`: `clean`. Child plan; Set `ioegmo`; `- Blocks-Release: next` inherited from backlog `ioegmo` (graduated).

Verified:
- `tests/test_clean_target_config_home.py` method `test_case_l_tracked_install_still_writes_target` at HEAD contains no `files changed` literal. Commit 84cba788c ("fix(ci): derive test_case_l expectation ...") replaced the `--stat` tail check with `commit_paths == tracked_paths` (`git show --name-only` vs `git ls-files` minus `README.md`), non-empty, `AGENTS.md`, `.aw/.gitignore`, and an empty `git status --porcelain`. That is the plan's own OQ-01 fallback oracle. `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py -k test_case_l` gave `1 passed, 22 deselected` (measured while reviewing sibling `3nczai` this sweep).
- F2 ("the test currently fails in this lane", 363 vs 358) is stale at HEAD.
- Sibling plan `3nczai` (backlog `6i9viq`, same defect) was reviewed in this sweep and rescoped to verify 84cba788c and add the missing sensitivity proof.
- Probe of the E-01 oracle question: `.created-files.json` is NOT an exact oracle for an install's commit set. An accidental private-target install (incident below) produced a record of 100 paths against 104 staged changes. The record omits modified pre-existing files (6 `M` paths, including `.gitignore`, `GEMINI.md` and `.aw/config/project.json`), and it lists 2 paths that are ignored and so never staged (`.aw/system/layout.json`, `.aw/system/layout.schema.json`). That fits `engine.save_created_files_record` recording only newly CREATED files, while `engine.prompt_and_run_commit` also commits modified ones. In a fresh target the only modified files are ones the installer itself creates first, so the mismatch would be smaller there, but the record still is not a drop-in set-equality oracle.

INCIDENT, recorded so that the report is honest. While probing E-01, the reviewer ran `aw install . --preset private-target -y` with its working directory resolved to the REVIEW LANE rather than the scratch target, because the shell had not changed directory. The install staged 104 paths and wrote untracked files into the lane. It made no commit: the lane HEAD was unchanged and the install reported "Changes are STAGED but NOT committed". The reviewer reversed it precisely. It unstaged and restored the 6 modified tracked files from HEAD. It removed the 98 added paths from the index. It then deleted only paths whose birth time fell inside the install window and that HEAD does not track (`.agents/`, `.agent-workflows-installer-backups/`, `.aw/state/durable/`, `.aw/workflow-artifacts/`, `.aw/records/{comms,prompts}/untracked/`, `.aw/setup-repo-needed.md`, `.aw/config/local.json`, `.aw/system/layout*.json`, two `.gitkeep`s). Files outside that window were left untouched (`.aw/state/lane-inputs/`, `.aw/state/mypy-cache/`, `.aw/records/plans/INDEX.*`, `.opencode/`). Afterwards `git status --short` was empty. The backup copies of the 4 backed-up files were byte-identical to HEAD, which confirms nothing pre-existing was lost.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Executability (false premise / duplicate carrier) | `git show 84cba788c -- tests/test_clean_target_config_home.py`; F2; E-02 "replace `self.assertIn("358 files changed", tail)`" | The defect this plan fixes is already fixed at HEAD, by its own OQ-01 fallback oracle. E-02 has nothing to replace and V-02's diff demand cannot be satisfied. Sibling `3nczai` already carries the verification and sensitivity work. Executing this plan would duplicate it or fabricate evidence. | C:Low; U:Low; S:Low; F:Low; Overall:High (foundational: whether the plan should exist at all is a disposition decision) | OPEN | Escalated as OQ-02 (`- Blocking: yes`, `- Finding: PR-001`). Recommended: retire to `superseded/` and close `ioegmo` on `3nczai`'s evidence. |
| PR-002 | MEDIUM | IN-SCOPE | Correctness (oracle assumption) | Measured: `.created-files.json` 100 entries vs 104 staged paths; `engine.save_created_files_record` | The preferred oracle in E-01/E-02 omits modified files and lists ignored ones, so it does not equal the commit set. Any rescope that adopts it needs an explicit adjustment design. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | Depends on OQ-02. If it is retired, the finding is moot. If it is rescoped, the oracle must be redesigned. Recorded and not fixed in place, because editing E-01/E-02 would pre-empt the OQ-02 decision. |

`aw ipd lint --phase review-finalize --agent`: `error` `IPD-Q501` (OQ-02 blocking and open). This is the intended stop.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Rescope this plan in place, as was done for sibling `3nczai`? | No. Escalate to the maintainer. | Rescope to verification (REJECTED: it would duplicate `3nczai` and create two carriers for one fix); retire it here (REJECTED: retirement is a disposition decision for the human, and outside a review's authority). | `3nczai` review this sweep; AGENTS.md retirement rule. | yes |

No decision is `Reversible: no`. PR-001 (HIGH, OPEN) is escalated as OQ-02 with `- Blocking: yes` and `- Finding: PR-001`.
