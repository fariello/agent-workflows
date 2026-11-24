# Review findings: plan bebahq

- Subject-Id: bebahq
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `b5dcb3275` in a runner review-sweep lane worktree (non-interactive). The plan was committed and unmodified (last plan commit `61b7a48f3`), so no pre-review snapshot was taken. Before revisions, `aw ipd lint --phase author` reported 2 info advisories (`IPD-C802`) and no errors or warnings. After revisions it reported 3 advisories (`IPD-Z603` for 6 E-items, plus the same 2 `IPD-C802`) and no errors or warnings. Reviewed against backlog `83kkzh`, spec `4sd62s` (4.4, 4.5a, 4.6 Orphans, 4.9.4, AC-33), and `agent_workflows/artifact_meta.py` (`State`, `ReadAtResult`, `resolve_mirror_at`, `_load_legacy_at_blob`, `read_at`, `check_staged_log_append`, `LEGACY_LOADER_VERSION`, `compute_schema_hash`, `open_cache`, `_cache_rev_write`, `read_text`, the three strict mirror parsers). Also reviewed: every production `read_at` caller in `agent_workflows/check_engine.py`, `agent_workflows/hooks/executed_transition_gate.py`, `agent_workflows/hooks/meta_log_append_gate.py`, `agent_workflows/hooks/ipd_dependency_statement_gate.py`, `agent_workflows/runner_shared.py`, and `agent_workflows/status_set.py`; `agent_workflows/meta_cli.py::_parse_log_backed_mirror`; and the fixtures in `tests/test_meta_log_append_gate.py`, `tests/test_cutover_log_gates.py`, `tests/test_readers_read_at_gates.py`, `tests/test_readers_gate_cache_parity.py`, and `tests/test_artifact_meta_read.py`. Baseline rerun at review: `python3 -m pytest -o addopts="" --no-cov tests/test_artifact_meta_read.py tests/test_readers_read_at_gates.py tests/test_migrations_chain.py` gave `47 passed in 9.02s`.

`AW-TIER: standard`
`AW-REVIEW: DONE`

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Scope IN/OUT, Scope-Paths | Only `artifact_meta.py` and two test files; OUT called `6jd6mh` "pending" | Adds the log-only reader, the 4 caller switches, the cache-version bump, and `tests/test_cutover_log_gates.py`; `6jd6mh` named as executed | PR-001, PR-002 |
| Project conventions | Stated `dataclasses.replace` as a fallback beside the SQL join | Treats the join as the contract, with in-memory assembly; adds caller-count, cache-invalidation, and `@repo/` bullets | PR-001, PR-002, PR-004, PR-007 |
| Findings | F-05 cited baseline `b7a0b2376` only | F-05 adds the review rerun; new F-06, F-07, and a caller-impact table | PR-001, PR-002, PR-006 |
| E-02 | Fallback return undefined; no cache invalidation | Defines the uncached `(id, status, True)` return; skips the `_load_legacy_at_blob` write; bumps `LEGACY_LOADER_VERSION` to `legacy_v11` | PR-002, PR-003 |
| E-03 | "via `rel_repo`"; warm path implicit; join plus fallback | Extracts `_read_log_state_at`; joins on warm and cold paths; handles `@repo/`; `mirror-` error prefixes; join assembled on disk or in memory | PR-001, PR-004, PR-005, PR-007 |
| New E-06 / V-06 | None | Moves 4 log-judging callers to `_read_log_state_at`, with 2 new gate tests | PR-001 |
| E-04, E-05, Required tests, V-04 | Three regression files | Six files, including `tests/test_meta_log_append_gate.py`, `tests/test_cutover_log_gates.py`, `tests/test_readers_gate_cache_parity.py`; dependencies on E-06 | PR-001 |
| V-02, V-03 | Diff hunks only | Add the version bump, fallback, legacy-write skip, cache-rebuild test, warm/cold and `@repo/` hunks | PR-002, PR-003, PR-004, PR-005 |
| Proposed changes, flowchart, Deferred, Scope check, Scope fence | Five steps, three paths | Adds E-06 and the accepted skip-on-corrupt callers with reasons | PR-001 |

#### Issues

- `IPD-C802` (line about the reachability rule): an em dash in boilerplate the plan inherited; advisory only and left unchanged.

### Step T

1. Yes: `read_at` is the shared revision reader for the commit gates and hooks, and its result for v2 records changes from `ok` to `corrupt` on a mirror fault; `State` gains a field.
2. Yes: the change alters what the pre-commit gates (`ipd-executed-gate`, `meta-log-append-gate`, the commit-invariant drift rule) accept.
3. No: 6 E-items in one task group, but four modules change.
4. Yes: no `.spec.md` path in Scope-Paths.
5. Medium: wrong handling makes post-cutover gates fail open (drift unreported) or refuse valid commits; pre-cutover repositories carry no `meta/*.jsonl` logs, so they are unaffected.

Tier: standard.

### Step R1

- Checked: F-01 to F-04 hold. The v2 branch of `read_at` returns right after `rev_log_states` on both the warm cached-row path and the cold replay path, and never resolves the `.md` blob. `State` has no `mirror_status`. `resolve_mirror_at` calls `read_text(text)` without `record_type` and inserts into `rev_mirrors` unvalidated. The three named fixtures write logs without `.md` files.
- Missed: `read_at` has 13 production callers. Once `read_at` returns `corrupt` on a mirror fault, `check_staged_log_append` refuses with "loader refused staged log", and `check_staged_meta_mirror_drift`, `_staged_log_only_executed_transitions`, and `terminal_log_refusals` skip the record. That makes the drift rule fail open on exactly the faults it exists to report (PR-001).
- `_load_legacy_at_blob` also writes `rev_mirrors`, and rows already on disk survive because `open_cache` rebuilds only on a `compute_schema_hash` change (PR-002).

### Step R2

- Checked: E/V bijection (6/6 after revision). Every V-item demands pasted diffs and runner output. `Item-Dependencies: none` is correct for Order 1 of a one-child Set. `From-Backlog: 83kkzh` and `Blocks-Release: next` are inherited.
- `tests/test_meta_log_append_gate.py::_seed_committed_log` commits logs with no `.md` mirror, so its 18 tests depend on how `check_staged_log_append` reads; the file was missing from the regression list (PR-001).
- F-05 cited a baseline commit that is not the lane HEAD (PR-006).

### Step R3

- Checked: the fail-closed direction is correct per spec 4.4 step 3 and the 4.6 Orphans rule. The risk is in the callers, not in `read_at`, and PR-001 covers it. No new subprocess, path, or input surface: the `.md` blob is read through the existing `_git_blob_sha` and `_read_git_blob_bytes` helpers.
- No further security finding.

### Step R4

- Checked: A data model: no table change, and the join on `l.id6 = m.id6` works with the 4.5a columns. C: `resolve_mirror_at` must still return `exists=True` with best-effort values on an invalid mirror, or the drift rule and `executed_transition_gate` lose their drift report; the plan left this undefined (PR-003). D invariants: `state.path` may be records-relative or `@repo/...`, and E-03 said only "via `rel_repo`" (PR-004). The warm `rev_log_states` hit returns early, so the join must run there too (PR-005). F smallest design: a log-only reader shared by the four log-judging callers is smaller than special-casing a `mirror-` error in each of them, and it keeps `read_at` itself strictly fail-closed. G: the spec says `read_at` "joins this table with `rev_log_states`", so the join is the contract; the SQL join and the in-memory `dataclasses.replace` are two ways to build the same `State` (PR-007). Spec sync: no amendment, because the plan implements 4.4 and 4.5a as written.

### Step S5

- Checked: no question needs a human. Fail-closed behavior is required by spec 4.4. The caller handling, cache invalidation, and fallback contract are resolved from repository evidence and recorded as decisions D-1 to D-3. The hook modules belong to executed plan `6jd6mh`, and this plan changes only which reader they call.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | C compatibility / D invariant | `agent_workflows/artifact_meta.py::check_staged_log_append` (staged `read_at` non-ok refuses "loader refused staged log"); `agent_workflows/check_engine.py::check_staged_meta_mirror_drift` (`if res.kind != "ok" ... continue`); `agent_workflows/hooks/executed_transition_gate.py::_staged_log_only_executed_transitions` (`continue`); `agent_workflows/hooks/meta_log_append_gate.py::terminal_log_refusals` (`return []`); `tests/test_meta_log_append_gate.py::_seed_committed_log` | Making `read_at` fail closed on mirror faults, as the spec requires, would make four log-judging callers either refuse valid appends or silently skip drift and terminal-log checks, and would break `tests/test_meta_log_append_gate.py`. The plan had no caller-impact analysis. | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | Caller-impact table under Findings; E-03 extracts `_read_log_state_at`; new E-06/V-06 switches the four callers and adds two gate tests; regression list widened to six files. |
| PR-002 | MEDIUM | IN-SCOPE | D invariant (cache) | `agent_workflows/artifact_meta.py::compute_schema_hash` hashes `LAYOUT_VERSION`, `LEGACY_LOADER_VERSION` (`"legacy_v10"`), and the registry; `open_cache` rebuilds only on hash change; `_load_legacy_at_blob` writes `rev_mirrors` keyed by `md_blob_sha` | Unvalidated `rev_mirrors` rows already in a user's `index.db` would survive the fix and be served as valid mirrors. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 bumps to `legacy_v11` with a comment line and skips the `_load_legacy_at_blob` write for log-backed blobs; V-02 demands a cache-rebuild test. |
| PR-003 | MEDIUM | IN-SCOPE | C compatibility | `agent_workflows/check_engine.py::check_staged_meta_mirror_drift` (`if not exists: continue`); `agent_workflows/hooks/executed_transition_gate.py` mirror reads; `agent_workflows/meta_cli.py::_parse_log_backed_mirror` `read_text` fallback | The plan did not define what `resolve_mirror_at` returns when strict v2 parsing fails; returning `exists=False` or `None` values would hide drift. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 returns `(fallback.id6 or None, fallback.status, True)` from `read_text(text, record_type=art_type)` with no cache write. |
| PR-004 | MEDIUM | IN-SCOPE | D invariant (paths) | `agent_workflows/artifact_meta.py` stored-path helpers (`@repo/` prefix); `agent_workflows/check_engine.py::check_staged_meta_mirror_drift` (`sp[len("@repo/"):]` else `rec_prefix + sp`) | `state.path` may be `@repo/...`; "via `rel_repo`" would build a wrong git path and fail every extra-root record as `mirror-missing`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 states both conversions, matching the drift rule; V-03 demands the `@repo/` hunk. |
| PR-005 | LOW | IN-SCOPE | G executability | `agent_workflows/artifact_meta.py::read_at` warm `rev_log_states` hit returns early | E-03 did not say the join also runs on a warm `rev_log_states` hit, so an executor could fix only the cold path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and its expected outcome name warm and cold paths. |
| PR-006 | LOW | IN-SCOPE | Evidence | F-05 cites `b7a0b2376`; review lane HEAD `b5dcb3275`; rerun `47 passed in 9.02s` | The baseline commit was stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 records both runs; V-01 re-records on the executor's HEAD. |
| PR-007 | LOW | IN-SCOPE | F simplicity | Spec `4sd62s` 4.5a ("`read_at` joins this table with `rev_log_states`"); `agent_workflows/artifact_meta.py::_cache_rev_write` | The SQL join plus a separate `dataclasses.replace` "fallback" read as two code paths; they are one contract built two ways. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and Project conventions describe one joined result assembled from disk rows or in memory. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How do log-judging callers survive a fail-closed `read_at`? | A private log-only reader `_read_log_state_at`, used by the four callers that judge the log | Special-case a `mirror-` error in each caller (rejected: four copies of one rule); keep `read_at` fail-open (rejected: violates spec 4.4) | Spec 4.4 step 3; caller-impact table; `6jd6mh` rules judge log events, not the mirror | yes |
| D-2 | How are poisoned `rev_mirrors` rows removed? | Bump `LEGACY_LOADER_VERSION` to `legacy_v11` | Delete rows at open (rejected: new code path); document `aw index rebuild` (rejected: silent until run) | `compute_schema_hash` and `open_cache` rebuild rule; existing `legacy_vN` bump convention | yes |
| D-3 | What does `resolve_mirror_at` return on an invalid v2 mirror? | `exists=True` with best-effort id and status, uncached | Return `(None, None, True)` (rejected: drift rule reports false id drift); `exists=False` (rejected: hides the file) | `meta_cli._parse_log_backed_mirror` precedent | yes |
| D-4 | Skip-on-corrupt callers `check_staged_illegal_backlog_transition` and `_staged_ipd_overlay` | Leave unchanged | Make each refuse on mirror faults (rejected: the drift rule reports the same fault in the same commit after E-06) | Caller-impact table | yes |
| D-5 | Review tier | standard | simple | Step T answers 1 and 2 yes, 5 medium | yes |
