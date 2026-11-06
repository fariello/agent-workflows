# Review findings: plan t4gl15

- Subject-Id: t4gl15
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `c75030b70` in a non-interactive runner review-sweep lane worktree, after the same lane reviewed `ffceq0`. The lane-input copy (revision 11) is byte-identical to the tracked plan. The plan was committed and unmodified, so no pre-review snapshot was needed. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| D-1, E-11 | Every reader returns the normalized status | Plans only; other types keep their raw token, following `ffceq0` D-1 as amended | PR-001. |
| D-4 (new), E-07, ledger | Loose runner whitespace not addressed | The runner keeps `-  `/`-\t` tolerance through `read_text`'s loose values | PR-002. |
| E-05, spec sync, Scope-Paths | The hook compares HEAD and staged log bytes itself | The hook calls one `artifact_meta.check_staged_log_append`; spec 4.3 amended | PR-003. |
| E-04, V-04 | `tests/test_status_set.py -k head` | `-k untooled` plus a new HEAD-status setter case | PR-004. |
| Pin-first rule, V-02 to V-12 | Summary-line count comparisons, combined `-k` commands | Outcome lists under `.aw/state/t4gl15/`; new-module `-k` runs separate | PR-005. |
| E-07, V-06, V-07 | `/tmp/discover_before.txt`; "1,719 records today" | Saved under `.aw/state/t4gl15/`; equality except named D-1 lines | PR-006. |
| E-01, E-09, E-10, E-15, V-01, V-15, V-16 | Baselines "before" with no capture item | E-01 saves `aw check all` counts and the three `aw index --check` results | PR-007. |
| E-12 | `read_readiness` in `review_tier` | `ipd_schema.read_readiness` in `review_rereview` (the real call) | PR-008. |
| E-11, Scope-Paths | `reviews` named but not in Scope-Paths | `reviews.py` added with its functions | PR-009. |
| Gate, E-15 | Partial execution contract | Full contract and the dash rule for `CHANGELOG.md` | PR-010. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. The plan adds a hook leaf (`aw meta-log-append-gate`), changes multi-word status answers (D-1) and, after this review, amends spec `4sd62s` 4.3.
2. Yes. It moves the pre-commit gates (`executed_transition_gate`, `status_untooled_gate`, `backlog_blocking_close_gate`) and runner merge-stage readers; it edits no sandbox or leak-sanitizer module.
3. Yes. It has 16 E-items in 5 task groups across about 30 modules.
4. Yes. It declares Scope-Paths.
5. Yes. A gate that reads a different status than before could let an untooled transition into `executed/` through.

AW-TIER: complex

### Step R1

- Checked: every symbol in Scope (b) and (c), the four hooks' helpers, the `check_engine` git readers and the `runner_shared` git readers by import and `hasattr`. All resolve except `plan_readiness.read_readiness`; the call is `ipd_schema.read_readiness` in `review_rereview` (PR-008). Every existing test module named exists.
- `_blob_text(` is called 14 times in `check_engine`, once in `hooks/ipd_dependency_statement_gate` and once in `status_set`, consistent with F-01/F-02.
- `hooks/executed_transition_gate` holds `git show` and two inline `^-` regexes (`_has_executed_status` case-insensitive, `_plan_id_of` strict), as the ledger says.
- `runner_shared.parse_plan_file` reads through `selectors.read_front_matter_status` (loose whitespace, single token) and falls back to the directory bucket. Measured: `discover_plans` returns 1,720 records; one differs from its normalized value (`vfa1tl`, `EXECUTED`); the 24 multi-word plans already resolve to `executed` through the bucket.
- `tests/test_status_set.py -k head` collects 0 tests (PR-004).
- `tve77h` E-07 makes the loader "the only code that opens a `meta/*.jsonl` log"; spec 4.3 says "No other code, inside or outside `artifact_meta`, opens a log" (PR-003).
- `artifact_audit.read_declared_status` serves every type (PR-001).
- The engine hook template ids are `ipd-executed-transition-gate`, `ipd-status-untooled-gate`, `backlog-blocking-close-gate`, `ipd-dependency-statement-gate`, as stated.
- F-09: `research_index._doc_entry` computes `has_body` from text after the front matter, and `derive_pipeline_positions` uses it, as stated.

### Step R2

- Checked: the E/V bijection is 16/16.
- Several V-items combined `-k` with baseline module paths, which filters the baselines too; summary counts miss pass-to-fail swaps (PR-005). `/tmp` baselines are lost on integration (PR-006). E-09, E-10, E-15 compared with "before" results no item captured (PR-007).
- Reachability: V-05's hook is produced by E-05; V-13's gates by E-02/E-03; V-08 by E-08.
- `- Item-Dependencies: executed:tve77h, executed:xexn45, executed:ffceq0` is correct (OQ-01).

### Step R3

- Checked: the gates stay fail-closed; an invalid staged record fails closed (E-13). Delegating the log judgement to the loader (PR-003) keeps one validation path, so a hook cannot accept what the loader refuses. No secrets or network (E-14).

### Step R4

- A: reads only, plus one read-only hook.
- C: one loader for logs (PR-003); one status rule per type (PR-001).
- D: pin-first outcome diffs; D-1 to D-4 name every behavior change. The runner's loose-whitespace contract, pinned by `test_parse_plan_file_tolerates_loose_leading_whitespace`, had no source after the move (PR-002).
- E: each group has a new module; the HEAD-status setter read gets a direct case (PR-004).
- Spec sync: "No spec change" became false with PR-003; now declared with its reason.

### Step R5

- Checked through the eight personas: QA (deterministic diffs), testing (no vacuous selections), UX (hook teaching message), architect (no log reads outside the loader), engineer (real symbols), power user (`aw oc run` queue unchanged except the named record), novice (refusals name the record), stakeholder (AC split with `ffceq0` unchanged).

### Step R6

- Checked: 16 E-items in 5 groups. E-07 is the densest; OQ-03 records a 07a/07b split. No split recommended (D-3).

### Step R7

- Checked against `ffceq0` as hardened in this lane: D-1 is now plans-only and `read_text` returns strict and loose values; this plan now cites both (PR-001, PR-002). `tve77h` E-14 (`read_at` for index and commits) and E-07 (loader-only log reads) are consistent with OQ-02 and E-05. `9o83cr` E-12 deletes `_blob_text`, `_status_meta`, `_front_matter_bullets`, `review_findings._META_RE` and `plans_index._META_RE`, matching this plan's Deferred list. `cxxmyv` E-05 takes the post-cutover gate forms.

### Step S5

- Checked: OQ-01 to OQ-03 are resolved and non-blocking. The E-05 spec amendment is decided from spec 4.3 (D-1 below). No question needs the human.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R4 D / R7 | D-1 "every reader returns the canonical normalized status"; `plans.normalize_status("open") == "legacy/unknown"`; `artifact_audit.read_declared_status` serves every type | Applied to non-plan records, the runner's spec and backlog reads and the audit reader would turn valid statuses into `legacy/unknown`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | D-1 limited to plans, following `ffceq0` D-1 as amended. |
| PR-002 | HIGH | IN-SCOPE | R4 D | `tests/test_front_matter_loose_whitespace.py::test_parse_plan_file_tolerates_loose_leading_whitespace`; `tve77h` E-11 strict grammar | Once moved, the runner's pinned loose-whitespace behavior had no source. | Low | FIXED | D-4: the runner uses `read_text`'s loose values when the strict value is absent. |
| PR-003 | MEDIUM | IN-SCOPE | Spec 4.3 / R3 | E-05 "compare `read_at`'s HEAD blob with the staged blob"; spec 4.3 "No other code ... opens a log" | The hook would parse log bytes outside the loader. | Low | FIXED | One `artifact_meta.check_staged_log_append` function; spec 4.3 amended; declared in Scope-Paths and spec sync. |
| PR-004 | MEDIUM | IN-SCOPE | R2 evidence | `python3 -m pytest --co tests/test_status_set.py -k head` collects 0 | The HEAD-read pin selected no tests. | Low | FIXED | `-k untooled` (5 tests) plus a new HEAD-status setter case. |
| PR-005 | MEDIUM | IN-SCOPE | R2 / R4 D | V-09 "`-k plans tests/test_plans_index.py ...`"; "equal counts" | `-k` filtered the baseline modules; count equality misses pass-to-fail swaps. | Low | FIXED | Outcome-list diffs; new-module `-k` runs separate. |
| PR-006 | MEDIUM | IN-SCOPE | R2 G live counts | V-06 "`/tmp/discover_before.txt`", "(`1719` entries)"; measured 1,720 | A lost baseline and a live count used as the bar. | Low | FIXED | `.aw/state/t4gl15/`; equality except the named D-1 lines. |
| PR-007 | MEDIUM | UNDER-SCOPE | R2 | E-15 "equal to the pre-E-02 baseline"; E-09/E-10 "same result as before" | No item captured those baselines. | Low | FIXED | E-01 saves them. |
| PR-008 | LOW | IN-SCOPE | R1 | E-12 "`read_readiness`" for `review_tier`; the call is `ipd_schema.read_readiness` in `review_rereview` | Wrong attribution. | Low | FIXED | Corrected. |
| PR-009 | LOW | IN-SCOPE | R2 scope fence | E-11 moves `reviews` subject resolution; `agent_workflows/reviews.py` absent from Scope-Paths | Undeclared file. | Low | FIXED | Added with the functions it changes; D-1 test files added too. |
| PR-010 | MEDIUM | UNDER-SCOPE | S7 contract | Gate text | The gate lacked the honesty rule, the `git add -A` ban, the fence-as-declaration wording and conditional finalize ownership. | Low | FIXED | Full gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the staged-log append judgement live? | An `artifact_meta` function; spec 4.3 amended | Hook reads log bytes (violates 4.3); hook diffs bytes and calls `read_text` per line (a second log path) | Spec 4.3 "No other code ... opens a log"; `tve77h` E-07 | yes |
| D-2 | Normalize non-plan statuses? | No | Normalize all types | `plans.normalize_status` vocabulary; `ffceq0` D-1 as amended | yes |
| D-3 | Split E-07 or the plan? | No | Split at OQ-03's 07a/07b seam | One pin set per E-item; 16 items in 5 groups | yes |
