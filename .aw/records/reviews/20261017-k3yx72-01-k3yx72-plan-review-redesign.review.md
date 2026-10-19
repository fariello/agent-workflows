# Review findings: spec k3yx72

- Subject-Id: k3yx72
- Subject-Type: spec
- Reviewed-At: 2026-10-18
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `36bcd71ba` in an interactive session. The spec was at `draft`, named explicitly by id6
(admitted per `25kzda` 2.5a), committed and unchanged, so no pre-review snapshot was needed. Structural
preflight `aw specs check` conformed (exit 0) before and after revisions. `aw ipd lint` was never run
against the spec; no `- Readiness:` was written; status and history were left to `aw specs set` /
`aw specs note`.

Re-measured: `ipd_schema.MAX_E_LEAVES = 18`, `MAX_TASK_GROUPS = 5`; `review_findings.parse_review_text`
reads rows only under an H3 starting `Findings`/`Decisions`; `plan_readiness.review_staleness_index`
keys on the `plan-review:` subject prefix; `runner_shared` fallback subject
`review({host_label}): record the review of {id6}` present; `runner_shared.perform_defect_reask`,
`probe_reply_text`, `classify_probe_reply` (first-line + both-sentinel rule) present;
`check_engine._carrier_is_executed` present; `25kzda` 2.6 "never join the frozen run" present; `4sd62s`
is `reviewed` with `Blocks-Release: next`; `20260802-1904` 10.2 and `IPD-C801` advisory confirmed. Cost
figures (1,311 attempts, 16.05B tokens, $10,528) match `tmp/20261017-runs-analyze-review-cost.prompt.md`,
which is gitignored. `aw ipd set superseded --dry-run` relocates a plan today. `ipd_schema.OQ_HEADING_RE`
requires two digits, and `has_unresolved_blocking_question` returned False for this spec with `OQ-2`
marked blocking.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-001 | HIGH | IN-SCOPE | 4.2, 5.3, 7.2, 8 | spec Section 5.3 table (`S5+S6+S7` in each tier's last prompt); Section 8.2 triggers computed after that prompt | S7 (Readiness, status, verdict entry, commit) ran in the same prompt as S6, before the runner could decide on another pass. Pass 1 could leave `reviewed` + `go` for a plan already scheduled for re-review; an interruption or `--full-auto` would then treat an unfinished review as done, and a second pass would add a second verdict entry and `plan-review:` commit, contradicting 7.2 and old AC 6. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Maintainer chose MD-15: verdict outputs once, at loop end; S7 is its own prompt; MD-14 counts +1; new S6/pre-S7 guard postcondition, AC-06/AC-07; "one entry" clarified as one VERDICT-BEARING entry, progress entries allowed. |
| SR-002 | HIGH | IN-SCOPE | 9.1 | spec Section 9.1 `completed-negative` row; `25kzda` 3.2 `to-review` row; `plan-review.md#Write the structured Readiness field`; 14 superseded + 4 not-executed plans carry `reviewed`-era `Readiness: no-go` | `completed-negative` left a no-go plan at `to-review`, silently amending `25kzda` 3.2 and making the runner (`run_selection_policy._IPD_ACTIONS` `to-review` -> review) re-review every no-go plan on every run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Maintainer chose MD-16: `reviewed` + `no-go` as today; orchestrator-exhaustion stays `to-review`. Added Section 9.4 (AW-MATERIAL marker + reviewed-contract hash test -> `recheck-readiness` or targeted re-review), AC-09/AC-10, Order 05 scope. |
| SR-003 | MEDIUM | IN-SCOPE | 13.5 | spec Section 13.5 "a difference smaller than about two times is not treated as real" | Decision rule had no outcome for the likely no-real-difference case, and quality was planted-defect count only. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Maintainer chose MD-17: pilot, recorded sample-size calc, sized run under a human cap; paired equivalence test; quality rubric; `single-12` on tie or cap; margins/rubric/cap in OQ-10 (blocking for Order 09). |
| SR-004 | MEDIUM | IN-SCOPE | 14 | spec Section 14 (old list 1-13); `89xjll` 3.2 acceptance namespace | Acceptance criteria had no stable ids (spec is post-`89xjll` cutover; TRACE needs `AC-*`), G3 had no criterion, and refusal paths for P re-ask, loop exhaustion, and split failure were missing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten as AC-01..AC-17 with requirement back-references, evidence statement, failure paths, and AC-16 for G3. Note on TRACE extraction of G/R ids added to Section 0. |
| SR-005 | MEDIUM | IN-SCOPE | 16 | `ipd_schema.OQ_HEADING_RE` (`^### (OQ-[0-9]{2,}):`); spec `### OQ-2:` | One-digit question ids are invisible to the approval gate, so "Blocking: yes" on OQ-2 had no effect, and a spec-level blocking flag cannot block a single Order. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renumbered to OQ-02/07/08/09 with a note; OQ-02 resolved by maintainer (MD-18: `` `path` "text" `` plus `\"`/`\\` escapes); proposed-target marking deferred to Order 03's plan as blocking there. |
| SR-006 | MEDIUM | IN-SCOPE | 10 step 4 | spec Section 10 "No such command exists today"; `status_set.py` block commented "When a child plan is retired"; `aw ipd set superseded --dry-run` | The claim that no tooled retirement exists is false: `aw ipd set superseded` relocates and records history; only the `RETIRED` header is missing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 4 and Order 06 now use the existing setter and add only the header. |
| SR-007 | LOW | IN-SCOPE | 0, 4.1, 7.2, 9.3 | spec "content digest", "review-staleness digest" | Undefined hash terms; 7.2 implied `Review-Depth` needed exclusion from a digest that never covers metadata (`ipd_lifecycle.frozen_region_digest` covers Scope-Paths + E/V action text only). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Defined plan-file hash and reviewed-contract hash in Section 0 and used them throughout. |
| SR-008 | LOW | IN-SCOPE | 1, 13.2 | `.gitignore` `tmp/`; spec Section 1 problem 1 | The motivating cost measurement lives only in a gitignored file, so the evidence is not durable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Source named and marked non-durable; analytics backlog item must carry the figures. |
| SR-009 | LOW | IN-SCOPE | 6 S7 | `ipd_lint.check_open_questions` (IPD-Q501 at every checkpoint) | S7's "no new lint error" postcondition would fail every legitimate `no-go` that adds a blocking question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Exempted IPD-Q501 for blocking questions S5 added or kept. |
| SR-010 | LOW | IN-SCOPE | 9.2, 16 OQ-08 | spec 9.2 "Section 13 variable V3"; `agent_workflows/` module list | Wrong variable cross-reference (session is V4); OQ-08 candidates not named as paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reference corrected; candidates listed as verified module paths. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Escape rule for `` `path` "text" `` when the text contains `"` | `\"` and `\\` only | JSON string; forbid quotes | Maintainer chose form (1); a citation must stay unambiguous; minimal escape set | yes |
| D-2 | Default `review_variant` before the experiment concludes | `single-12` | `grouped-6` | Maintainer: prefer single-12 on a tie for per-step information | yes |
| D-3 | Treat a malformed `AW-MATERIAL:` after one re-ask as | `yes` (re-review) | `no` | Missed re-review costs more than an unneeded one | yes |
| D-4 | Enforcement of the pre-S7 verdict-output guard | detect-and-restore, recorded as OQ-11 for Order 04 | permission denial | Non-goal N2; host-neutral | yes |
