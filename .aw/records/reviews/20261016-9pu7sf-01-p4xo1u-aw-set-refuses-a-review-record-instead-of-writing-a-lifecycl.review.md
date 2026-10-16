# Review findings: plan p4xo1u

- Subject-Id: p4xo1u
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at `a178320e9`. The plan was committed and unchanged (`d284020a7`), so no snapshot was needed. `aw ipd lint --phase author` and `--phase review-finalize` were both clean.

Re-verified with throwaway probes under the gitignored `.aw/state/` (deleted afterwards):
- Against current code, in a temp repo holding only the review: (a) `set approved <path>` gives rc 0 and the file is rewritten; (b) the same with `--dry-run` gives rc 0 and the file is unchanged; (c) `set other approved <path>` gives rc 0, rewritten; (d) `set to-review <relative path>` from the repo cwd gives rc 0, rewritten. `ipd set`, `specs set`, `backlog set` give rc 2 `Type mismatch`. A bare id6 gives rc 2 `No artifact matched`.
- `selectors.NON_PRIMARY_RECORD_DIRS == {'reviews'}`. A monkeypatched equivalent of E-02 (path under any `selectors.record_dirs(repo, t)` for `t` in that set, refused right after `match_selector`) gave rc 2 on (a)–(d), with the file byte-identical and `git status --porcelain` empty.
- Positive control: `set parked <backlog path>` gives rc 0, and the item moves to `backlog/parked/` reading `- Status: parked`.
- `run_set_command` call sites: `backlog.py`, `specs.py`, `work_cmd.py`, `cli.py` ×3, `status_set.py`, so the refusal covers every setter spelling.
- `artifact_types.py` docstring lines 21–22 carry the quoted "does not yet refuse a review path (backlog `9pu7sf`)".

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate said "move the plan to `executed/` via the tooled lifecycle". It had no OQ status line, no scope-fence declaration, no hard-MUST paste rule, and no conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all of these. |
| PR-002 | MEDIUM | IN-SCOPE | B/C. Test isolation | `tests/support.py::init_repo`, `clean_git_env` | The E-01 fixture ran raw `git` without scrubbing inherited git env vars, so a run inside a hook or lane could write to the outer repo. Case (d) changes cwd with no stated restore. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now uses `init_repo`/`clean_git_env` and restores cwd in `finally`. |
| PR-003 | LOW | IN-SCOPE | E. Evidence precision | review probe (b): rc 0, file unchanged | E-01 said each review case fails as "exit 0 and/or file changed", but the dry-run case does not change the file. V-01's executor should know which assertion fails. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records the measured per-case failure mode and requires no `slow` mark (so CI collects it). E-02 cites the review demonstration of the mechanism. |
| PR-004 | LOW | UNDER-SCOPE | D. Coverage claim | `backlog.py`/`specs.py`/`work_cmd.py`/`cli.py` call `run_set_command` | "Every spelling ... is tested" rested on F-04, which named only `ipd set`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 0 records the shared funnel; F-04 now cites re-measured `ipd`/`specs`/`backlog set` refusals. |
| PR-005 | LOW | IN-SCOPE | Records conformance | `## Workflow history`; OQ-01 `Owner: none`; E-05 `aw commit <plan>` | The history was oldest-first, the resolved OQ had no owner, and the commit command used a placeholder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Newest-first; `Owner: plan author`; `aw commit p4xo1u`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should the refusal go: the setter or `detect_artifact_type`? | Keep the plan's choice: the setter | Retype in `detect_artifact_type` (changes `artifact_audit`'s `plans` fallback and six other callers) | plan F-03; review probe of the setter placement | yes |
| D-2 | Is the HOW (path-under-`record_dirs` check) demonstrated? | Yes | Leave as a spike E-item | monkeypatched probe: rc 2, byte-identical, clean porcelain | yes |
