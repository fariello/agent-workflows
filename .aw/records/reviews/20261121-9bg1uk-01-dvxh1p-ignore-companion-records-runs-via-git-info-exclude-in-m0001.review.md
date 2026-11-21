# Review findings: ipd dvxh1p

- Subject-Id: dvxh1p
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261121T064614Z-2150223`). The target plan `.aw/records/plans/pending/20261119-9bg1uk-01-dvxh1p-ignore-companion-records-runs-via-git-info-exclude-in-m0001.ipd.md` was committed and unchanged, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` errors, `0` warnings, `2` non-blocking `IPD-C802` info advisories on the template `Validation-state rule` boilerplate). Inspection of backlog `9bg1uk`, artifact metadata store spec `4sd62s` (`Section 5.2a`, `AC-18`, `AC-42`), `agent_workflows/migrations/m0001_metadata_v2.py`, `agent_workflows/migrations/m0001_preflight.py`, `agent_workflows/project_context.py`, `agent_workflows/runner_shared.py`, `agent_workflows/ipd_lifecycle.py`, `tests/migration_corpus.py`, `tests/test_m0001_layout_stage.py`, `tests/test_m0001_any_repo.py`, and `CHANGELOG.md` (plus an empirical probe of `git check-ignore -q -- records/runs/` against nonexistent paths) surfaced one `HIGH`, one `MEDIUM`, and two `LOW` findings (`PR-001..PR-004`), all fixed in place. Pass 2 re-checked the complete revised plan for internal consistency across `Concern`, `Scope`, `Goal`, `E-01..E-04`, `V-01..V-04`, `Findings`, `Proposed changes`, the Mermaid diagram, `Spec / documentation sync`, and `Approval and execution gate`.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Approval and execution gate` | Single paragraph with implicit finalize wording, no resolved-OQ precondition, no `--scope-reason`/`--scope-ack` variance rule, no honesty rule, no shared-checkout rule, no hand-`git mv` prohibition, and inline backlog closure | Structured bulleted execution contract covering resolved-OQ precondition, `--scope-reason`/`--scope-ack` variance rule, hard-MUST paste-actual-runner-output honesty rule, shared-checkout safety, conditional runner/executor `aw ipd finalize dvxh1p` with explicit hand-`git mv` prohibition, and post-finalization separation for closing backlog `9bg1uk` | PR-001, `steps/r2-executability.md`, `steps/s7-finalize.md` |
| `E-02`, `Proposed changes`, `V-02` | Tested `companion_backend` apply, `.gitignore` override, `repository` backend, and `home` backend ("without writing a lock-directory exclude entry") without testing dry-run non-mutation or noting `.gitignore` commit / `/.aw/state/` nuance | Added `companion_backend` dry-run (`apply=False`) non-mutation check, specified committed `companion/.gitignore` in case (b), and clarified in case (d) that the assertion checks for no `runs/` exclude entry (since `/.aw/state/` may still be written when the target repo lacks `.aw/.gitignore`) | PR-002, `steps/r4-engineering.md` |
| `E-03`, `E-04`, `V-03`, `V-04`, `Required tests / validation` | `E-03`/`V-03` hardcoded "five" `CORPUS_SHAPES` cases; `V-04` omitted pasted output for the targeted pytest run (`test_m0001_preflight.py`) and omitted `--phase pre-transition --agent` on `aw ipd lint` | Changed `E-03`/`V-03` to require all parameterized `CORPUS_SHAPES` cases; added the targeted pytest run output and `aw ipd lint --phase pre-transition --agent` to `E-04`/`V-04` and `Required tests / validation` | PR-003, `steps/r2-executability.md` |
| `Concern`, `Scope`, `Goal`, `E-01`, `E-04`, `F-02`, `F-03`, `Proposed changes`, `Deferred`, `Scope check`, `Spec / documentation sync`, `Open questions` | Used abbreviated `module.symbol` citations, truncated `CHANGELOG.md` heading `## 2.0.0 (pending)`, internal function name `project_context.record_git_root` in user-facing changelog text, and unlabelled `spec 4sd62s Section 5.2a / AC-18` | Qualified citations to `path::Symbol`, cited the exact `CHANGELOG.md#2.0.0 (pending) - AW project layout, storage backends, install wizard, and operational state` heading, made the `CHANGELOG.md` bullet plain user-facing prose, updated Mermaid step E to note `OSError`/`ValueError` guard, and named spec `4sd62s` topic plus `AC-42` | PR-004, `steps/p-proofread.md` Section 11.1, technical writing standard Requirements 1 and 12 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes; changes `aw migrate metadata --apply` behavior for external companion repositories by writing `<git_common_dir>/info/exclude` in the companion repository and tightens the `AC-42` companion cleanliness assertion relied on by `tests/test_m0001_any_repo.py`.
2. No; touches only `agent_workflows/migrations/m0001_metadata_v2.py`, two migration test files, and `CHANGELOG.md`, with no private-data sanitizer, commit helper, worktree isolation, merge-to-main, or sandbox code.
3. No; small and focused (`4` E-items in `1` task group across `1` production module, `2` test files, and `CHANGELOG.md`).
4. Yes; `- Scope-Paths:` explicitly lists all `5` files (`agent_workflows/migrations/m0001_metadata_v2.py`, `tests/test_m0001_layout_stage.py`, `tests/test_m0001_any_repo.py`, `CHANGELOG.md`, and this plan).
5. Yes; a mistake computing `rel_runs` or gating `info/exclude` writes could write an overly broad ignore pattern (such as `/` or `/.`) into a companion repository's `info/exclude` or regress `repository`/`home` migration behavior.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261117-metastore-01-9bg1uk-ignore-companion-records-runs-via-git-info-exclude.backlog.md`, spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (`Section 5.2a`, `AC-18`, `AC-42`), `agent_workflows/migrations/m0001_metadata_v2.py` (`_append_git_info_exclude`, `_ensure_state_gitignored_via_exclude`, `_resume_applying_journal`, `run`), `agent_workflows/migrations/m0001_preflight.py` (`acquire_apply_integration_lock`, `_check_uncommitted_records`), `agent_workflows/project_context.py` (`record_git_root`), `agent_workflows/runner_shared.py` (`integration_lock_path`, `runs_repo_root`, `state_root`), `agent_workflows/ipd_lifecycle.py` (`checkout_git_common_dir`), `agent_workflows/attention.py` (`_resolve_runs_repo_root`), `tests/migration_corpus.py` (`companion_backend`), `tests/test_m0001_layout_stage.py` (`test_companion_backend_external_records_root_in_place_migration_and_query`, `test_home_backend_external_records_root_in_place_migration_and_query`), `tests/test_m0001_any_repo.py` (`CORPUS_SHAPES`, `test_ac42_corpus_shapes_end_to_end_migration`), and `CHANGELOG.md`.
- Verified every referenced symbol, file path, and spec anchor exists and behaves as described; empirically probed `git check-ignore -q -- records/runs/` against nonexistent paths for empty, `records/runs/`, `records/runs`, `/records/runs/`, and `runs/` `.gitignore` entries (`returncode` `1` when unignored, `0` for all four ignored forms).
- Found abbreviated symbol citations, truncated `CHANGELOG.md` heading reference, and missing `AC-42` mention in `Spec / documentation sync` (`PR-004`). Fixed in place.

### Step R2

- Checked: `E-*`/`V-*` bijection (`4/4`: `E-01..E-04` <-> `V-01..V-04`, `- Highest E allocated: 04`), dependency chain (`E-01 -> E-02, E-03 -> E-04`), `- Scope-Paths:` completeness, `- Item-Dependencies: none`, runtime reachability of `V-01..V-04` (all demand diffs, search exits, or real test/CLI runner outputs, reachable by construction), and `Approval and execution gate`.
- Found incomplete execution contract in `Approval and execution gate` (`PR-001`) and `E-04`/`V-04` targeted-pytest evidence alignment plus hardcoded `CORPUS_SHAPES` count in `E-03`/`V-03` (`PR-003`). Fixed in place.

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). `_ensure_state_gitignored_via_exclude` operates only on local git paths resolved through `runner_shared.integration_lock_path` and `project_context.record_git_root`, passes `--` before the path argument in `subprocess.run(["git", "-C", str(lock_git_root), "check-ignore", "-q", "--", f"{rel_runs}/"])` (preventing flag injection), guards `OSError`, `ValueError`, empty string, and `"."` (preventing writing a root-wide ignore pattern into `info/exclude`), and performs no network calls, credential handling, or sensitive data logging.

### Step R4

- Checked: correctness and data integrity (`_append_git_info_exclude` is idempotent and `git check-ignore` returns `0` on subsequent calls; `checkout_git_common_dir` safely returns `None` if `lock_git_root` is not a valid git repository; `record_git_root` resolves paths before walking parents so `relative_to` succeeds across symlinks and nonexistent `runs/` directories), anti-regression (preserves `repository` backend `/.aw/records/runs/` behavior, `.gitignore` overrides, and `home` backend no-op), testing completeness (`PR-002` adds dry-run `apply=False` non-mutation check, committed `.gitignore` fixture detail, and explicit `home`-backend assertion scope distinguishing `runs/` from `/.aw/state/`), right-sizing (`4` cohesive single-concern E-items, `5` Scope-Paths), and `## Spec / documentation sync` (aligned with `4sd62s` `Section 5.2a`, `AC-18`, `AC-42`, and `CHANGELOG.md`).

### Step S5

- Checked: `## Open questions` (`None.`). Every finding (`PR-001..PR-004`) has `Overall:Low` Remediation Risk and is settled directly by repository evidence and backlog `9bg1uk`. Zero blocking or human-owned questions remain.

### Pass 2

- Re-checked the complete revised plan across front matter, `Goal`, `E-01..E-04`, `Step 0`, `Findings`, `Proposed changes`, Mermaid diagram, `Deferred / out of scope`, `Scope check`, `Required tests / validation`, `Spec / documentation sync`, `Open questions`, `V-01..V-04`, and `Approval and execution gate`.
- Verified `4/4` E/V bijection, `- Highest E allocated: 04`, `- Status: reviewed`, `- Readiness: go-pending-approval`, `- Review-Depth: standard`, newest-first `/plan-review` history entry, zero open questions, and clean `aw ipd lint --phase review-finalize --agent` disposition.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261119-9bg1uk-01-dvxh1p-ignore-companion-records-runs-via-git-info-exclude-in-m0001.ipd.md:152-157; .aw/system/workflows/plan-review/steps/r2-executability.md:57-60; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | `Approval and execution gate` omitted required execution-contract clauses (resolved-open-questions precondition, `--scope-reason`/`--scope-ack` scope-fence variance rule without stopping over scope variance, hard-MUST paste-actual-runner-output honesty rule, shared-checkout safety rule, explicit hand-`git mv` prohibition, and explicit both-branch conditional runner/executor `aw ipd finalize dvxh1p` ownership) and placed backlog `9bg1uk` closure inline with finalization without marking it as a separate post-finalization step outside `- Scope-Paths:`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` with all required execution-contract clauses, explicit conditional runner/executor `aw ipd finalize dvxh1p` ownership, hand-`git mv` prohibition, and separate post-finalization backlog `9bg1uk` closure. Recommendation strength: very strong. |
| PR-002 | MEDIUM | UNDER-SCOPE | R4 / Testing coverage & fixture invariants | .aw/records/plans/pending/20261119-9bg1uk-01-dvxh1p-ignore-companion-records-runs-via-git-info-exclude-in-m0001.ipd.md:43,96,138; agent_workflows/migrations/m0001_metadata_v2.py::_ensure_state_gitignored_via_exclude:576-591; tests/test_m0001_layout_stage.py::test_home_backend_external_records_root_in_place_migration_and_query:580-628 | `E-02` and `V-02` did not verify that dry-run (`apply=False`) on `companion_backend` leaves `<companion_common_dir>/info/exclude` untouched; did not note committing `companion/.gitignore` in case (b); and did not clarify in case (d) (`home` backend) that `<repo_common_dir>/info/exclude` may still receive `/.aw/state/` when the target repository lacks `.aw/.gitignore`, so the assertion must verify no `runs/` exclude entry rather than an untouched `info/exclude`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-02`, `Proposed changes`, and `V-02` to include the `companion_backend` dry-run non-mutation check, specify a committed `companion/.gitignore` in case (b), and specify checking for no `runs/` lock-directory entry in case (d). Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | R2 / E-V alignment & count stability | .aw/records/plans/pending/20261119-9bg1uk-01-dvxh1p-ignore-companion-records-runs-via-git-info-exclude-in-m0001.ipd.md:48-55,142-149; tests/test_m0001_any_repo.py::CORPUS_SHAPES:40 | `E-04` ran `python3 -m pytest tests/test_m0001_layout_stage.py tests/test_m0001_any_repo.py tests/test_m0001_preflight.py`, but `V-04` did not require pasting that targeted pytest output (leaving `tests/test_m0001_preflight.py` unverified in `V-*`) and omitted `--phase pre-transition --agent` on `aw ipd lint`; `E-03`/`V-03` also hardcoded the count "five" for `CORPUS_SHAPES`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the targeted pytest output and `aw ipd lint --phase pre-transition --agent` checkpoint to `E-04`, `Required tests / validation`, and `V-04`, and updated `E-03`/`V-03` to require all parameterized `CORPUS_SHAPES` cases to pass. Recommendation strength: strong. |
| PR-004 | LOW | IN-SCOPE | Proofreading / R1 / Technical writing standard | .aw/records/plans/pending/20261119-9bg1uk-01-dvxh1p-ignore-companion-records-runs-via-git-info-exclude-in-m0001.ipd.md:5-6,30,38,53,75-76,102-110,122,126; CHANGELOG.md:7; .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:301 | Multiple code citations used abbreviated `module.symbol` names instead of `path::Symbol`; `E-04` cited truncated heading `## 2.0.0 (pending)` and put internal identifier `project_context.record_git_root` into user-facing `CHANGELOG.md` prose; and `Spec / documentation sync` omitted spec `4sd62s`'s topic and `AC-42`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Qualified citations to `path::Symbol`, cited the exact `CHANGELOG.md` heading, rewrote the `CHANGELOG.md` bullet in plain user-facing language, updated Mermaid step E to note the `OSError`/`ValueError` guard, and named spec `4sd62s`'s topic plus `AC-42`. Recommendation strength: strong. |

### Decisions

None.
