# Review findings: plan t4gl15

- Subject-Id: t4gl15
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
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

## Round 2

This re-review ran at HEAD `0b49e5c6e` in an isolated runner review-sweep lane worktree after the 2026-11-07 approval withdrawal and reader split (`h58z9n`, `y97k46`, `jd7874`, `2zpw22`), and the 2026-11-09 round-3 split (`jq82as`). Working tree was clean at turn start (`pre-review snapshot: skipped unchanged`). Pass 1 and Pass 2 verified the post-split plan against amended spec `4sd62s`, orchestrator `63ib9r`, the reviewed split parts, and current repository gates. Before edits, `aw ipd lint --phase author` returned clean with two non-blocking `IPD-C802` em-dash advisories; after revisions, `aw ipd lint --phase review-finalize --agent` returned clean (`0` errors, `0` warnings, `0` advisories).

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted narrow unsafe-condition stop rule and conditional runner/executor finalize clause | Added explicit stop-and-report rule for absent prerequisite symbols, baseline failure, or checkout conflicts, and explicit conditional runner/executor ownership clause | PR-001, Technical Writing Standard Requirement 1. |
| Open questions (OQ-01, OQ-02, OQ-03) | Recorded `- Owner: none` on resolved questions | Updated to `- Owner: plan author` (OQ-01, OQ-02) and `- Owner: maintainer` (OQ-03), and recorded decisions in `### Decisions` (D-1, D-2, D-3) | PR-002, steps/s5-questions.md owner attestation standard. |
| Proposed changes (ordered, validatable) | One-line description without process diagram | Added Mermaid `flowchart TD` diagram showing execution progression across E-13, E-14, and E-15 | PR-003, Technical Writing Standard Requirement 12(b). |
| Step 0 / Project conventions discovered | Cited code using unqualified `module.function` symbols | Standardized citations to repo-relative `path::Symbol` identifiers | PR-004, Technical Writing Standard Requirement 7, IPD-C801. |
| Validation and cross-check / Front matter | Contained em dashes (U+2014) in V-rule prose and omitted front matter readiness | Replaced em dashes with parentheses resolving two `IPD-C802` advisories, and added `- Readiness: go-pending-approval` | PR-005, Technical Writing Standard Requirement 1, Step S7 review output requirements. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. The plan owns AC-1a (gate cache parity) and AC-12 (offline proof), adds `tests/test_readers_gate_cache_parity.py`, adds a `CHANGELOG.md` entry for the new hook, and closes the repository-wide residual regex audit (F-04).
2. Yes. It exercises pre-commit gates (`aw ipd-status-untooled-gate`, `aw ipd-executed-gate`, `aw backlog-blocking-close-gate`, `aw ipd set`) that guard repository commits and lifecycle transitions.
3. No on execution item count after splitting (`3` E-items in `1` task group), yes on cross-module audit scope (E-15 audits residual `^-` regexes across 24 functions in 12 modules and verifies 5 cited tables).
4. Yes. `- Scope-Paths:` explicitly declares `tests/test_readers_gate_cache_parity.py`, `CHANGELOG.md`, and the plan itself.
5. Yes. Gate cache parity verification failure or residual audit omission could mask regressions in commit gates or lifecycle checks.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (sections 4.4, 4.8, 5.2a, 6, 7); orchestrator `63ib9r`; split parts `h58z9n` (Order 33), `y97k46` (Order 34), `jd7874` (Order 35), `2zpw22` (Order 36), `jq82as` (Order 141), `snh19k` (formerly `h58z9n`), `ffceq0` (Order 08); and gate test modules in `tests/`.
- Verified resolved open questions OQ-01, OQ-02, and OQ-03 owners: updated from `- Owner: none` to `- Owner: plan author` (OQ-01, OQ-02) and `- Owner: maintainer` (OQ-03) (`PR-002`).

### Step R2

- Checked: E/V bijection (`3/3`: `E-13..E-15` <-> `V-13..V-15`), `- Highest E allocated: 16`, `- Item-Dependencies:` (`executed:2zpw22, executed:jq82as, executed:ffceq0, executed:g5hpbb, executed:h58z9n, executed:jd7874, executed:tve77h, executed:xexn45, executed:y97k46`), and isolated-lane reachability of every `V-*` demand.
- Checked gate contract: added narrow unsafe-condition stop rule and explicit conditional runner/executor finalize ownership clause to `Approval and execution gate` (`PR-001`).
- Verified zero em/en dashes, explicit state directory initialization (`mkdir -p .aw/state/t4gl15`), and valid `- Scope-Paths:`.

### Step R3

- Checked: E-13 tests gate parity across cold, warm, deleted, and corrupt caches; E-14 asserts offline execution without network access (`PATH` stripped of host launchers, `socket.socket` patched to raise).
- Gates remain fail-closed on corrupt or unparseable records.

### Step R4

- A (Correctness and data integrity): Idempotent tests; cache parity proves deterministic behavior regardless of cache temperature or corruption.
- C (Architecture and operability): Reuses existing test patterns and gate CLIs (`aw ipd set`, `aw ipd-status-untooled-gate`, `aw ipd-executed-gate`, `aw backlog-blocking-close-gate`).
- D and E (Anti-regression and testing): Pin-first discipline preserved; cache-parity tests prevent regression during metastore migration; residual audit F-04 ensures no unowned `^-` regexes or `Workflow history` readers linger in production modules.
- Executability and right-sizing: 3 E-items in 1 task group after the 2026-11-07 and 2026-11-09 splits; each item addresses one cohesive deliverable.

### Step R5

- Checked through the eight review personas: QA/QC (deterministic parity tests across cache states), testing/regression (untainted offline environment proof), UI/UX (clear gate failure diagnostics naming invalid records), architect (one metadata cache loader across all gates and hooks), software engineer (exact CLI leaves and parameters), power user (consistent pre-commit gate verdicts), novice (unambiguous gate rejection reasons), stakeholder (AC-1a, AC-12, and residual audit F-04 closure).

### Step R6

- Checked: 3 E-items in 1 task group across 2 non-plan Scope-Paths (`tests/test_readers_gate_cache_parity.py`, `CHANGELOG.md`), well within right-sizing bounds after the splits. No further decomposition needed.

### Step R7

- Checked consistency across the `Set: metastore` family: child plan `t4gl15` aligns with orchestrator `63ib9r`, Order 08 `ffceq0`, split reader parts `h58z9n`, `y97k46`, `jd7874`, `2zpw22`, append hook carrier `jq82as`, and writer finisher `xexn45`. Shared dependencies in `- Item-Dependencies:` accurately reflect the split decomposition.

### Step S5

- Checked: OQ-01, OQ-02, and OQ-03 are resolved and non-blocking. Attested owners set and decisions D-1 through D-5 recorded in `### Decisions`. Zero questions belong to the human (`questions: []`).

### Step S6

- Re-review check: No new `E-*` or `V-*` items added or removed; `- Scope-Paths:` and `- Item-Dependencies:` unchanged; all edits are surgical hardening.
- Re-run `aw ipd lint --phase review-finalize --agent` confirmed clean (0 errors, 0 warnings, 0 advisories).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261102-metastore-09-t4gl15-move-runner-gate-hook-and-module-reads-onto-artifact-meta-an.ipd.md:231 | Approval and execution gate omitted explicit narrow unsafe-condition stop rule and explicit conditional runner/executor finalize clause. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added narrow stop rule for missing prerequisites, baseline test failure, or checkout conflicts, and explicit conditional runner/executor ownership clause to Gate (recommendation strength: strong). |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ owners | .aw/records/plans/pending/20261102-metastore-09-t4gl15-move-runner-gate-hook-and-module-reads-onto-artifact-meta-an.ipd.md:186 | OQ-01, OQ-02, and OQ-03 recorded `- Owner: none` on resolved questions, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `- Owner: plan author` (OQ-01, OQ-02) and `- Owner: maintainer` (OQ-03) and recorded decisions in `### Decisions` (D-1, D-2, D-3) (recommendation strength: strong). |
| PR-003 | LOW | IN-SCOPE | Proofreading / Requirement 12(b) | .aw/records/plans/pending/20261102-metastore-09-t4gl15-move-runner-gate-hook-and-module-reads-onto-artifact-meta-an.ipd.md:120 | Proposed changes lacked a Mermaid diagram required by Technical Writing Standard Requirement 12(b) for multi-step processes with branches. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram under `## Proposed changes` showing execution progression across E-13, E-14, and E-15 (recommendation strength: strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Requirement 7 / Step 0 | .aw/records/plans/pending/20261102-metastore-09-t4gl15-move-runner-gate-hook-and-module-reads-onto-artifact-meta-an.ipd.md:67 | Step 0 cited code using unqualified `module.function` symbols instead of repo-relative `path::Symbol` identifiers (`IPD-C801`, Technical Writing Standard Requirement 7). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Standardized code citations to `path::Symbol` identifiers in Step 0 (recommendation strength: strong). |
| PR-005 | LOW | IN-SCOPE | Proofreading / Advisory IPD-C802 / Step S7 | .aw/records/plans/pending/20261102-metastore-09-t4gl15-move-runner-gate-hook-and-module-reads-onto-artifact-meta-an.ipd.md:209 | Line 209 contained em dashes (U+2014) in V-rule prose triggering `IPD-C802` advisories; front matter lacked `- Readiness: go-pending-approval`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced em dashes with parentheses in line 209 and added `- Readiness: go-pending-approval` to front matter (recommendation strength: very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does this plan depend on Order 08 (`ffceq0`)? | Yes. Retain `executed:ffceq0` in `- Item-Dependencies:` because `t4gl15` needs `artifact_meta.read_text` and status normalization rule D-1. | Omit `ffceq0` dependency (rejected: `read_text` and D-1 are introduced in `ffceq0`). | OQ-01, spec `4sd62s` | yes |
| D-2 | How does `read_at` serve a merge-stage blob (`:<stage>:<path>`)? | First try `read_at(id6, ":<stage>:")`; fallback to `artifact_meta.read_text` over stage blob text if stage spelling is unsupported. | Build custom parser for merge stages (rejected: violates C5a single-loader requirement). | OQ-02, spec `4sd62s` C5a | yes |
| D-3 | Should the plan be split? | Handled by 2026-11-07 maintainer split into `h58z9n`, `y97k46`, `jd7874`, `2zpw22`, `jq82as`, and finishing plan `t4gl15` (3 E-items). | Further split `t4gl15` (rejected: 3 items in 1 task group is already well right-sized). | OQ-03, research `nj8zdp` | yes |
| D-4 | How is gate cache parity verified across cache states? | Run four distinct gate CLIs on fixture repository under cold, warm, deleted, and corrupt `.aw/state/index.db`, asserting identical normalized outputs and exit codes. | Run on live repository (rejected: corrupt cache would disrupt other lane operations). | `t4gl15` E-13, spec `4sd62s` AC-1a | yes |
| D-5 | How is offline execution proved without network access? | Strip host launcher binaries from `PATH` and patch `socket.socket` to raise via `sitecustomize` on `PYTHONPATH`. | Disable network adapter (rejected: unsupported in test runner). | `t4gl15` E-14, spec `4sd62s` AC-12 | yes |
