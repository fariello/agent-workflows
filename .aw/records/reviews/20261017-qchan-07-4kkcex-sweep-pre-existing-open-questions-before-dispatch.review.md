# Review findings: plan 4kkcex

- Subject-Id: 4kkcex
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `e1bc71233`. The plan was byte-identical to the lane input. `aw ipd lint --phase author --agent`: `clean`. Child plan. Prerequisites `mtmqlm` and `j0ufrj` are `reviewed`, not executed; their contracts were read from those plans.

Verified:
- `enforce_draft_admission_gate` has ONE call site, inside `runner_shared.initialize_run_core`, followed by `--with-dependencies`, `enforce_dependency_preflight`, `enforce_mixed_type_gate`, and only then `mint_run_dir`; `--prepare-only` returns from the same function.
- `prompt_for_gate_phrase` uses `select` and then `stdin.readline()`; `GATE_PROMPT_TIMEOUT = 180.0`. `is_interactive_run` returns False under `--unattended`/`--full-auto`.
- `ipd_lint.parse(text).open_questions` reads `### OQ-NN:` blocks under `## Open questions` only; `check_open_questions` is a linter over that list. `OQ_STATUS_VALUES` is `open`/`resolved`/`deferred`.
- Run flags are `runner_shared.RUN_POLICY_FLAGS` rows (`kind`, `resume_rule`, `RESUME_NONE_DEFAULT`), registered on both hosts from one table; spec `25kzda` 2.1 lists the grammar and the table comment says nothing derives or checks it.
- Path-scoped package commits go through `git_commit_helper.offer_commit`.
- Order 08 (`jshwxb`) declares `executed:4kkcex`, so `group_open_questions` cannot exist when this plan executes.
- Spec `6kwd2e` R1.1-R1.7, R7.1, R9.7, A1, A2, A14, A16, A18, A27, A28, A40, A41, A47 read as cited.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness (dependency and hook) | plan E-04 "hook into Order 04's `consume_answers`"; `Item-Dependencies: executed:mtmqlm` | E-04 modifies Order 04's `consume_answers` and relies on Order 02's parked status, but the plan depended only on `mtmqlm`; under parallel lanes it could run before `j0ufrj` exists. | all Low | FIXED | Added `executed:j0ufrj`. The orchestrator's child table still reads `executed:mtmqlm` for Order 07; it was NOT edited here because editing it stales its coverage record (`IPD-S408`, measured), so the orchestrator owner should reconcile that cell. |
| PR-002 | HIGH | IN-SCOPE | Correctness (held item semantics) | plan E-04 "treat the owning item like a parked item"; `j0ufrj` E-03 lane adoption | A pre-flight-held item has never run, so it has no lane or session; Order 04's resume path would refuse it (`fail-lane`) or adopt nothing. Non-blocking questions' effect on holding was unstated. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 marks `preflight_parked`, holds only on a blocking question, and on consumption writes the answer into the artifact and re-queues as a normal first attempt without `resume_with_answers`. |
| PR-003 | HIGH | IN-SCOPE | Correctness (seam and ordering) | `initialize_run_core` (single call site of `enforce_draft_admission_gate`; `mint_run_dir` later) | The plan said "both hosts, beside `enforce_draft_admission_gate`", which is one shared function, and placed the inbox write where no run directory yet exists. | all Low | FIXED | E-03 runs in `initialize_run_core` after every selection gate and before `mint_run_dir`, skipped on `--prepare-only`; E-04 routes after the run directory exists. |
| PR-004 | MEDIUM | IN-SCOPE | Correctness (prompt) | `prompt_for_gate_phrase` `stdin.readline()` after `select` | "reads available bytes non-blockingly" was underspecified; `select` then `readline()` can block on a partial line. Empty/EOF/length were undefined. | all Low | FIXED | E-02 loops `select` + `os.read` against a monotonic deadline, defines empty/EOF/timeout as None, caps at 4000 chars. |
| PR-005 | MEDIUM | IN-SCOPE | Data integrity (write-back) | plan E-03 "write it into the artifact immediately ... commit through `aw commit --no-plan`" | No writer was named, no staleness check (artifact edited during the sitting), and shelling to `aw commit` from inside the driver is not the package's commit path. | all Low | FIXED | `record_oq_answer` rewrites one block with a hash/state check; commit via `git_commit_helper.offer_commit` path-scoped; commit failure keeps the text and routes the question. |
| PR-006 | MEDIUM | IN-SCOPE | Executability (flags, parser, scope) | `RUN_POLICY_FLAGS`; `ipd_lint.parse`; Scope-Paths `ipd_lint.py` | Flags were to be hand-registered on both parsers; the parser was cited as `check_open_questions`; `ipd_lint.py` was in scope with no change needed. | all Low | FIXED | Flags as `RUN_POLICY_FLAGS` rows; collector uses `ipd_lint.parse`; `ipd_lint.py` removed from Scope-Paths; OQ-03 records the `25kzda` 2.1 grammar question. |
| PR-007 | MEDIUM | IN-SCOPE | Testing (A27 vs P16) | spec A27 "Assert statically (no `readline()` ...)"; AGENTS.md "NEVER ... read production source" | The plan claimed A27 coverage; its static half conflicts with the repository's test rule. | all Low | FIXED | Behavioral A27 (patched `input`/`readline` raise); deviation recorded (D-3). |
| PR-008 | LOW | IN-SCOPE | Process | OQ-01 `Owner: maintainer`; `-q` | Spec-settled OQ labelled maintainer; `-q` hides `N passed`; the Order 08 "if present" clause was misleading. | all Low | FIXED | Owner corrected (D-1); `-q` removed; OQ-02 explains ordering (D-4). |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Commit per answer or batched? (OQ-01) | Per answer. | Batched (REJECTED: loses answers on interrupt). | spec R1.7. | yes |
| D-2 | How is a pre-flight-held item released? | `preflight_parked` + write-back in `consume_answers`, re-queued as attempt 1. | Reuse Order 04 resume (REJECTED: no lane/session exists). | `j0ufrj` E-03; spec R3. | yes |
| D-3 | Satisfy A27's static grep? | Behavioral test only. | Source-reading test (REJECTED: AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE" / GUIDING_PRINCIPLES P16). | AGENTS.md. | yes |
| D-4 | Ordering before Order 08? (OQ-02) | Queue order, then OQ order. | Implement dedup here (REJECTED: Order 08 owns R4 and depends on this plan). | `jshwxb` `Item-Dependencies`. | yes |
| D-5 | Amend `25kzda` 2.1 for the two flags? (OQ-03) | No, add as policy rows. | Amend the spec here (REJECTED: not needed for correctness; maintainer may add later). | `6kwd2e` R1.2/R1.3; `RUN_POLICY_FLAGS` comment. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`. Follow-up for the orchestrator owner: update the Order 07 row's dependency cell in `wpv9r7` to include `executed:j0ufrj` and re-run `aw ipd coverage wpv9r7`.
