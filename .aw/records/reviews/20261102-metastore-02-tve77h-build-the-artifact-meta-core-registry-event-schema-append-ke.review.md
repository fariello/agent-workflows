# Review findings: plan tve77h

- Subject-Id: tve77h
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `73334d3e4` in a runner review-sweep lane worktree (non-interactive). The lane-input
copy (revision 2) is byte-identical to the tracked plan, which was committed and unmodified, so no
pre-review snapshot was needed. `aw ipd lint --phase author` reported clean with two `IPD-Z602` info
advisories (E-08, E-18), which the plan's Scope check already accepts.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-02, V-02 | Envelope lists `v`, `seq`, `append`, `at`, `actor`, `op` only | Adds optional `by_human` and `overrides` with their vocabulary and refusal tests | PR-001. |
| E-03, V-03 | Leak scan through the default ruleset "refuses a host name" | `include_warn=True` ruleset, any finding refuses, plus an absolute-path token rule, plus accepted relative-path and slash-command cases | PR-002. |
| E-05, V-05 | Every illegal edge refused | A plan terminal-reopen edge replays only under `overrides: [allow-terminal-reopen]` | PR-003. |
| E-01, E-17, V-01, V-17 | "`aw check` against a pre-E-01 baseline" that no item captures | E-01 saves `.aw/state/tve77h/check-before.jsonl`; E-17 and V-17 diff `(location, rule)` pairs against it | PR-004. |
| E-09, V-09 | "read-only state directory" fallback case | `index.db` replaced by a directory | PR-005. |
| Gate | Partial execution contract | Adds resolved-questions note, fence as declaration with `--scope-reason`/`--scope-ack`, no `git add -A`, honesty rule, runner vs hand finalize ownership | PR-006. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: it fixes the tracked event envelope, op payload schemas and field names that 4.2 calls "IRREVERSIBLE AFTER THE CUTOVER", and the `artifact_meta` interface that Orders 03 to 13 use by exact name.
2. Partly: no named guard module is edited, but E-03 is the writer's leak refusal for tracked logs (privacy) and E-14/E-16 drive git.
3. Yes: 18 E-items in 5 task groups, one new large module, six new test modules.
4. Yes: Scope-Paths lists the new module, `artifact_naming.py`, six test modules and the plan.
5. Additive phase A (no caller moves), so a mistake breaks no existing behavior; but a wrong envelope or field name becomes irreversible once Order 13 migrates the corpus with it.

AW-TIER: complex

### Step R1

- Checked by running the cited symbols in this lane: `artifact_core.ID6_RE` is `\A[0-9a-z]{6}\Z`; `attention_contract.SPEC_TRANSITIONS`, `BACKLOG_TRANSITIONS`, `refuse_unsafe_descriptive`, `MAX_DESCRIPTIVE_LEN` 300, `MAX_PROSE_DESCRIPTIVE_LEN` 4300, `newest_history_record`, `last_history_at` exist; `ipd_lifecycle.validate_transition("approved", "superseded")` returns `unknown target status 'superseded'` (F-12 holds) and `("executed", "draft")` is refused; `status_set.TYPE_STATUSES["plans"]` contains `superseded`, `not-executed`, `reusable`; `research_contract.STATUSES`, `lifecycle_dirs.LIFECYCLE_SUBDIRS["prompts"]`, `releases.RELEASE_STATUSES`, `releases.resolve_release_outcome` exist; `artifact_naming` has `_LEGACY_TIMESTAMP_RE`, `parse_clustered_prefix`, `parse_clustered` and no `parse_attributed`, and `parse_clustered` returns `None` on the V-11 D177 prompt name (F-05 holds; the file exists in `prompts/`); `ipd_schema.parse_item_dependencies(value) -> (edges, ready, error)`; `plan_readiness.VERDICTS` keys are the four gate verdicts; `review_findings.parse_review_text`, `project_context.resolve_project_context` (logical roots `config`, `records`, `state`, `system`), `project_context.record_git_root`, `platform_lock.acquire`/`held(path, *, blocking=False, timeout=None)`, `leak_sanitizer.build_ruleset`/`scan_text(..., include_warn=False)`, `runner_shared.utc_now`, `runner_shared.state_root` exist; `pyproject.toml` `dependencies = ["filelock>=3"]`; `sqlite3.sqlite_version` 3.45.1; `tests/test_artifact_naming_round_trip.py` exists; `artifact_meta.py` and `migrations/` are absent and no module imports `sqlite3`.
- Spec `4sd62s` checked against E-items: 4.2 envelope and `overrides` key (amended 2026-11-05, after this plan's 2026-11-02 authoring; PR-001), actor refusal list including host names (PR-002), 4.3 interface and LOADER VALIDATION, 4.5 and 4.5a table list and minimum indexes (E-08 matches), AC-4, AC-5, AC-17, AC-18, AC-23, AC-24, AC-26, AC-33, AC-39 text.

### Step R2

- Checked: E/V bijection 18/18; every V demands a named `-k` test run plus pasted values; reachability is by construction (tests the same plan writes). Scope-Paths covers all edits. `- Item-Dependencies: none` is correct (Order 02, additive; Order 01 is records-only and unrelated to the module). The E-17 baseline was demanded but never captured (PR-004). Live counts in F-02 to F-09 are context, not bars; no V uses them. The gate contract gap is PR-005/PR-006.

### Step R3

- Checked: E-03 is the only privacy surface; it writes tracked, cloned logs, so a leak there is permanent public history. Measured `leak_sanitizer.scan_text` on this machine: `ses_` plus 20 characters gives `session-id`; a home path gives `home-path`/`handle`; the user name gives `handle`; the host name gives NO finding with the default ruleset and `derived:<host>` `warn` only with `include_warn=True`; `/opt/x/a.md` gives no finding. Spec 4.2 requires host names and absolute paths to be refused. PR-002 fixed. SQL injection is covered by E-08 (`?` bindings, quoted registry identifiers). E-03 (c) path containment covers traversal.

### Step R4

- Checked: A, write order and commit point match 4.3 (E-15); `expect_seq` under the per-artifact lock; journal before commit for create and rename. C, reuses `atomic_write`, `platform_lock`, `project_context`, `parse_item_dependencies`, `run_analytics_cache` precedent; no new dependency. D, invariants mapped to named tests per E-item. E, failure injection, corruption, concurrency (two-branch merge) and companion-backend cases present; the read-only-directory case is not portable to the Windows CI leg or a root user (PR-005). F, an existing behavior replay must accept: `status_set` writes terminal-reopen edges under `--allow-terminal-reopen` that `ipd_lifecycle.validate_transition` refuses (`executed` -> `approved` measured refused), so a strict replay would make every reopened plan's log unreadable after the cutover (PR-003). Spec sync: "No spec change" is truthful.

### Step R5

- Checked through the eight personas: QA/testing, every behavior has a named failing case and the V-items require the case names; architect, single module per OQ-04 matches AC-1's evidence wording; engineer, interface names match those that Orders 03 and 06 to 10 cite (`read`, `history`, `query` with `depends_on`/`latest_gate_review_of`/`path` and `incomplete`, `resolve`, `read_at`, `append(id6, events, *, expect_seq)`, `create`, `repair(id6, *, confirm=None)`, `validate_new_events`, `replay`, `registry_fields`, `validate_event`); power user and novice, no user-facing surface in this plan; stakeholder, the irreversible envelope is now complete for the amended spec (PR-001). No further finding.

### Step R6

- Checked: 18 E-items and 5 task groups, at both size limits; the size lint passes. Per-item density: each E-item is one concern with one test module and one V; the largest (E-06 owned-field rules, E-10 freshness, E-15 write path) each name a single rule family. OQ-01 pre-records a 02a/02b seam. Splitting would add a plan and re-point seven dependents' `executed:tve77h` edges, without making any single item smaller. No split recommended (D-1).

### Step R7

- Checked: orchestrator `63ib9r` row 02 and completion criterion (owner `tve77h`, AC-4, AC-5, AC-8, AC-17, AC-18, AC-23, AC-24, AC-26, AC-33, AC-39) match this plan's OWNS table; dependents `1ajqaa`, `dcerjg`, `2xwb9b`, `xexn45`, `ffceq0`, `t4gl15`, `59aiyh` depend on `executed:tve77h`; functions added later by siblings (`read_text` by `ffceq0`, the legacy `append` branch and `LegacyRender` by `2xwb9b`, `write_legacy` by `xexn45`, `aw meta repair` by `ffceq0`) are owned there and need nothing here; `cxxmyv` E-01 adds `overrides` to the WRITER, which this plan's loader must accept (PR-001, PR-003); `dcerjg` E-13 replays produced logs through this plan's loader pointed at a scratch records root, consistent with E-09's resolved-root rule.

### Step S5

- Checked: OQ-01 to OQ-04 all resolved and non-blocking; each still holds after the revisions. No new question needs the human: every finding was fixed in place. Decisions below.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | R1/R7 spec sync | `4sd62s` 4.2 "`overrides`: a list of the override flags the setter was given"; history "2026-11-05 note ... event key overrides ... added to 4.2"; plan E-02 required-key list | The envelope omitted `by_human` and the `overrides` key added to the spec after authoring. 4.3 makes the loader refuse unknown fields, so every event `cxxmyv` E-01 writes with `overrides` would be refused, and the envelope is irreversible after the cutover. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 registers both optional keys with the closed `overrides` vocabulary; E-02 and V-02 test acceptance and refusal. |
| PR-002 | HIGH | IN-SCOPE | R3 privacy | `4sd62s` 4.2 "refuse ... absolute or home-directory file-system paths, user names and host names"; measured `leak_sanitizer.scan_text(<hostname>)` with default ruleset: no finding | E-03 used the default ruleset, which does not report host names, and the sanitizer reports no finding for a non-home absolute path. Leaked values would land in tracked, cloned logs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 uses `include_warn=True` and refuses on any finding, adds an absolute-path token rule that spares slash commands, and names the git root used for the ruleset; E-03 and V-03 add host-name, `/opt` path, relative-path and slash-command cases. |
| PR-003 | MEDIUM | IN-SCOPE | R4 F existing behavior | `ipd_lifecycle.validate_transition("executed", "approved")` -> "missing predecessor: backwards transition"; `status_set.py` "pass --allow-terminal-reopen" | Replay refused every edge the lifecycle table refuses, but setters write terminal-reopen edges today under an override. Those logs would be unreplayable after the cutover. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 accepts a plan edge out of `plans.TERMINAL` only with `overrides` containing `allow-terminal-reopen`; E-05 and V-05 test both sides. |
| PR-004 | MEDIUM | UNDER-SCOPE | G verification | plan E-17 "`aw check` against a pre-E-01 baseline" | No item captured the baseline, so E-17's comparison could not be produced honestly. | Low | FIXED | E-01 saves `.aw/state/tve77h/check-before.jsonl`; V-01 shows it; E-17 and V-17 diff `(location, rule)` pairs. |
| PR-005 | LOW | IN-SCOPE | R4 E portability | `.github/workflows/tests.yml` matrix `os: [ubuntu-latest, macos-latest, windows-latest]`; plan E-09 "a read-only state directory" | A `chmod` read-only directory is ignored by Windows and by root, so the fallback test would pass vacuously or fail on some legs. | Low | FIXED | The unopenable case is `index.db` replaced by a directory. |
| PR-006 | MEDIUM | UNDER-SCOPE | S7 execution contract | plan `## Approval and execution gate` | The gate lacked the honesty rule, the `git add -A` ban, the declaration wording with `--scope-reason`/`--scope-ack`, and conditional finalize ownership. | Low | FIXED | Gate rewritten. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Split the plan at the OQ-01 02a/02b seam? | No | Split now (adds a plan, re-points seven dependents, forces no-go per R6) | Each E-item is one concern with its own test module and V; size lint passes; OQ-01 resolution leaves the split optional | yes |
| D-2 | How should replay treat the terminal-reopen edge? | Accept only with `overrides` containing `allow-terminal-reopen` | Refuse always; accept any backward edge from terminal | `4sd62s` 4.2 `overrides` key; `status_set` terminal-reopen guard; 4.3 "a status transition that is not in the lifecycle table" refused otherwise | yes |
| D-3 | Which leak severities refuse in tracked logs? | Any finding (`fail` or `warn`) with `include_warn=True` | `fail` only (misses host names) | Measured scan results in Step R3; spec 4.2 refusal list | yes |
