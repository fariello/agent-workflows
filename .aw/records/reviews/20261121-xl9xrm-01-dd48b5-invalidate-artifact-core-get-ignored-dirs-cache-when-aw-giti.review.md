# Review findings: ipd dd48b5

- Subject-Id: dd48b5
- Subject-Type: ipd
- Reviewed-At: 2026-11-21
- Reviewer: antigravity/gemini-4-neon-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran in an isolated review-sweep lane worktree (`review-sweep-run-20261121T070301Z-2497766`). The target plan `.aw/records/plans/pending/20261121-xl9xrm-01-dd48b5-invalidate-artifact-core-get-ignored-dirs-cache-when-aw-giti.ipd.md` was committed and clean, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`0` findings). Inspection of backlog item `xl9xrm`, `agent_workflows/artifact_core.py` (`get_ignored_dirs`, `_cached_ignored_dirs`, `_is_repository_untracked_backend`, `is_ignored_path`, `iter_scan_files`, `SCAN_ROOTS`), subdirectory callers (`plans_index`, `plans_refs`, `research_index`, `research_refs`, `prompts_index`, `docs_check`), and `tests/test_records_untracked_backend.py` surfaced two `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-004`), all fixed in place. Pass 2 re-checked `Scope`, `Goal`, `E-01..E-02`, `Step 0`, `Findings`, `Proposed changes`, the Mermaid diagram, `Scope check`, `V-01..V-02`, and `Approval and execution gate` for full internal consistency.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| `Scope`, `E-01`, `Step 0`, `Scope check`, `V-01` | Checked `.git` and `.aw/.gitignore` only directly under `p` using `(st_mtime_ns, st_size)` without specifying relative `gitdir:`/`commondir` resolution or `OSError` guards | Added ancestor `.git` root discovery for subdirectory callers, relative/absolute `gitdir:` and `commondir` resolution with `OSError`/`ValueError` guards, and `(st_mtime_ns, st_size, st_ino)` stat tuples for atomic index/.gitignore replacements | PR-001, `steps/r1-references.md`, `steps/r4-engineering.md` |
| `Approval and execution gate` | Unconditionally instructed `aw ipd finalize` and omitted hand-`git mv` prohibition, resolved-OQ precondition, `--scope-reason`/`--scope-ack`, shared-checkout safety, and honesty rule | Added all required execution-contract clauses including conditional runner/executor `aw ipd finalize dd48b5` ownership | PR-002, `steps/r2-executability.md`, `steps/s7-finalize.md` |
| `E-02`, `Scope`, `V-02` | Tested only a standard `git init` repo with an empty `.aw/state/` directory and unspecified file under `.aw/records/`, with no worktree test | Added concrete `.aw/state/index.db` and scanned `.aw/records/plans/pending/...ipd.md` fixture details, added a real `git worktree add` invalidation test covering both worktree `index` and `commondir` `info/exclude`, and added zero-source-inspection constraint | PR-003, `steps/r4-engineering.md` |
| `Goal`, `E-01..E-02`, `Findings`, `Proposed changes` | Used abbreviated symbol references and lacked a Mermaid flowchart for the branched `.git`/worktree cache-key resolution | Qualified code citations to `path::Symbol` and added a Mermaid flowchart in `Proposed changes` per Requirement 12(b) | PR-004, `steps/p-proofread.md` Section 11.1, technical writing standard Requirement 12(b) |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No; internal cache-invalidation bug fix in `agent_workflows/artifact_core.py::get_ignored_dirs` and `_cached_ignored_dirs` with no CLI, output format, or spec contract changes.
2. No; touches only `agent_workflows/artifact_core.py` ignored-directory cache key and `tests/test_records_untracked_backend.py`, with no private-data, commit, worktree-isolation, merge, or sandbox code.
3. No; small and focused (`2` E-items in `1` task group across `1` production file and `1` test file).
4. Yes; `- Scope-Paths:` explicitly lists `agent_workflows/artifact_core.py`, `tests/test_records_untracked_backend.py`, and this IPD.
5. Yes; `agent_workflows/artifact_core.py::get_ignored_dirs` is called across 25+ sites (including repo-root callers, subdirectory callers, and worktrees), so a broken `.git` pointer parser or uncaught `OSError` would break scanning across the toolkit.

AW-TIER: standard

### Step R1

- Checked: backlog `.aw/records/backlog/graduated/20261121-xl9xrm-01-xl9xrm-artifact-core-get-ignored-dirs-caches-ignored-dirs.backlog.md`, `agent_workflows/artifact_core.py` (`DEFAULT_IGNORED_DIR_NAMES`, `_resolved_root_str`, `_is_repository_untracked_backend`, `_cached_ignored_dirs`, `get_ignored_dirs`, `is_ignored_path`, `iter_scan_files`, `SCAN_ROOTS`), all callers of `get_ignored_dirs` across `agent_workflows/`, and `tests/test_records_untracked_backend.py`.
- Found that `get_ignored_dirs` is invoked by subdirectory callers (`plans_index`, `research_index`, `prompts_index`, `docs_check`) as well as repo-root callers (`PR-001`), and that `E-01..E-02` used abbreviated symbol references (`PR-004`). All fixed in place.

### Step R2

- Checked: `E-*`/`V-*` bijection (`2/2`: `E-01..E-02` <-> `V-01..V-02`, `- Highest E allocated: 02`), dependency chain (`E-01 -> E-02`), `- Scope-Paths:` completeness, `- Item-Dependencies: none`, runtime reachability of `V-01..V-02` (both demand git diffs or real pytest/CLI outputs, reachable by construction), and `Approval and execution gate`.
- Found non-conforming execution contract in `Approval and execution gate` (`PR-002`: unconditional `aw ipd finalize`, missing hand-`git mv` prohibition, resolved-OQ precondition, `--scope-reason`/`--scope-ack`, shared-checkout safety, and honesty clauses). Fixed in place.

### Step R3

- Checked: security and privacy lens (`steps/r3-security.md` full form). Reading `.git` pointer files, `commondir`, and `os.stat` metadata is strictly local and read-only; guarding `gitdir:`/`commondir` reads against `OSError`/`ValueError` prevents crashes on malformed or transient git files without introducing new trust boundaries, subprocesses, or leaks.

### Step R4

- Checked: correctness and data integrity (`PR-001` adds ancestor `.git` root discovery, relative/absolute `gitdir:`/`commondir` resolution with `OSError` guards, and `st_ino` for same-tick atomic `.git/index` and `.aw/.gitignore` replacements), anti-regression and testing (`PR-003` specifies concrete `.aw/state/index.db` and `SCAN_ROOTS` `.md` fixture paths plus a real `git worktree add` invalidation test exercising worktree `index` and `commondir` `info/exclude`), right-sizing (`2` E-items, `3` Scope-Paths, cohesive single bugfix), and `## Spec / documentation sync` (`N/A` verified truthful).

### Step S5

- Checked: `## Open questions` (`None.`). Every finding (`PR-001..PR-004`) has `Overall:Low` Remediation Risk and is settled directly by repository evidence. Recorded `D-1` (ancestor `.git` walk + `(st_mtime_ns, st_size, st_ino)` stat tuple, `Reversible: yes`) in `### Decisions`. Zero blocking or human-owned questions remain.

### Pass 2

- Re-checked the complete revised plan across `Scope`, `Goal`, `E-01..E-02`, `Step 0`, `Findings`, `Proposed changes`, Mermaid diagram, `Scope check`, `Required tests / validation`, `V-01..V-02`, and `Approval and execution gate`.
- Verified `2/2` E/V bijection, `- Highest E allocated: 02`, zero unresolved questions, and clean `aw ipd lint --phase review-finalize --agent` disposition.
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | R1 / R4 / Subdirectory callers, worktrees, and atomic index stats | .aw/records/plans/pending/20261121-xl9xrm-01-dd48b5-invalidate-artifact-core-get-ignored-dirs-cache-when-aw-giti.ipd.md:38-44; agent_workflows/artifact_core.py::get_ignored_dirs:785-795; agent_workflows/plans_index.py:149; agent_workflows/research_index.py:226 | `E-01` checked `.git` and `.aw/.gitignore` only directly under `p` (missing subdirectory callers like `plans_index` and `research_index`), did not specify relative `gitdir:`/`commondir` resolution or `OSError`/`ValueError` guards, and used `(st_mtime_ns, st_size)` without `st_ino` (which catches equal-size atomic rename replacements like `.git/index.lock` -> `.git/index` within a coarse clock tick). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-01`, `Scope`, `Step 0`, `Scope check`, and `V-01` to walk ancestors for `.git`, resolve relative/absolute `gitdir:` and `commondir` with `OSError`/`ValueError` guards, and use `(st_mtime_ns, st_size, st_ino)` stat tuples (`D-1`). Recommendation strength: very strong. |
| PR-002 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261121-xl9xrm-01-dd48b5-invalidate-artifact-core-get-ignored-dirs-cache-when-aw-giti.ipd.md:108-113; .aw/system/workflows/plan-review/steps/r2-executability.md:57-60; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | `Approval and execution gate` unconditionally instructed running `aw ipd finalize` and omitted the explicit hand-`git mv` prohibition, resolved-open-questions precondition, `--scope-reason`/`--scope-ack` scope-fence variance rule, shared-checkout safety rule, and hard-MUST paste-actual-runner-output honesty rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote `Approval and execution gate` with all required execution-contract clauses and conditional runner/executor `aw ipd finalize dd48b5` ownership. Recommendation strength: very strong. |
| PR-003 | MEDIUM | UNDER-SCOPE | R4 / Testing coverage | .aw/records/plans/pending/20261121-xl9xrm-01-dd48b5-invalidate-artifact-core-get-ignored-dirs-cache-when-aw-giti.ipd.md:38-49,103-106; agent_workflows/artifact_core.py::SCAN_ROOTS:688-705; tests/test_records_untracked_backend.py:39-64 | `E-02` did not test the git worktree `.git`-file + `commondir` code path required by `E-01`, did not specify putting a file inside `.aw/state/` (so `git ls-files` reports `.aw`) or placing the tracked `.md` file under a `SCAN_ROOTS` directory (so `iter_scan_files` returns it), and omitted the zero-source-inspection constraint. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-02`, `Scope`, and `V-02` to specify concrete `.aw/state/index.db` and `.aw/records/plans/pending/...ipd.md` fixture paths, add a real `git worktree add` invalidation test covering worktree `index` and `commondir` `info/exclude`, and prohibit source-code inspection checks. Recommendation strength: strong. |
| PR-004 | LOW | IN-SCOPE | Proofreading / R1 / Technical writing standard | .aw/records/plans/pending/20261121-xl9xrm-01-dd48b5-invalidate-artifact-core-get-ignored-dirs-cache-when-aw-giti.ipd.md:30,38-49,61,63-67 | Plan used abbreviated symbol references instead of `path::Symbol` and omitted a Mermaid flowchart for the multi-step branched `.git`/worktree resolution flow (technical writing standard Requirement 12(b)). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Qualified symbol citations to `path::Symbol` and added a Mermaid flowchart in `Proposed changes` aligned with `E-01`. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `agent_workflows/artifact_core.py::get_ignored_dirs` locate git metadata and detect atomic index or `.aw/.gitignore` replacements? | Walk `(p, *p.parents)` to find the enclosing `.git` root, resolve both `.git/` directories and worktree `gitdir:`/`commondir` pointer files with `OSError`/`ValueError` guards, and key `_cached_ignored_dirs` on `(st_mtime_ns, st_size, st_ino)` tuples for `.gitignore`, `.aw/.gitignore`, `info/exclude`, and `index`. | Check only `p / ".git"` and `(st_mtime_ns, st_size)` (rejected: misses subdirectory callers such as `plans_index`/`research_index`, and equal-size atomic replacements within one coarse clock tick share `(st_mtime_ns, st_size)` while changing `st_ino`). | `agent_workflows/artifact_core.py::get_ignored_dirs:785`, `agent_workflows/plans_index.py:149`, `agent_workflows/research_index.py:226` | yes |
