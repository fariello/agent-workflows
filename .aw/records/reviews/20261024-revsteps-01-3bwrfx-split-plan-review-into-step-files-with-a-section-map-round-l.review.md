# Review findings: plan 3bwrfx

- Subject-Id: 3bwrfx
- Subject-Type: ipd
- Reviewed-At: 2026-10-25
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `185073ef7` in a runner lane worktree (non-interactive; human questions go to the
outcome file). The lane-input copy is byte-identical to the tracked plan, which was committed and
unmodified (`f10f8f3cd`), so no pre-review snapshot was needed. `aw ipd lint --phase author` and
`--phase review-finalize` conform before and after revisions. The one advisory, `IPD-Z602` on E-03,
was judged: E-03 is one deliverable (`p-proofread.md`) whose clauses are the contents of that file,
so it is not split.

Verified claims: `plan-review.md` is 48108 bytes / 741 lines (F-01). `Strong Recommend` appears
outside records only in `askme/askme.md` and `DECISIONS.md` prose, and no test pins it (F-02). The
three test modules E-16 names read `plan-review.md` through `support.section` with the headings the
plan names (`### G. Plan executability`, `### 3.1 Build the question set`), and
`test_v_item_evidence_durability.py` compares the "Live-artifact success criteria" bullet
byte-for-byte with `review-rubric.md` (F-03). `spec-review.md` and `spec-review/README.md` carry the
stale `plan-review.md:<n>-<m>` citations (F-04). `review_findings.parse_review_text` reads only under
`Findings`/`Decisions` H3s (F-05). `engine.collect_source_members` ships every file under the bundle
root, so `steps/` ships (checked: a scratch `aw install -y` took 3.4 s and installed only
`plan-review.md` and `README.md` today) (F-06). `wcisgc` exists under `prompts/reusable/` and has seven
numbered H2s. `00-run-protocol.md` has `## Review mindset: the eight reviewer personas`.
`tests/test_spec_review_attestation.py` forbids `plan-review/_generated`; `steps/` is not that.
`.opencode/commands/plan-review.md` and `.claude/commands/plan-review.md` point at the unchanged body
path. `plan_readiness.VERDICTS` holds the four tokens E-10 and E-17 name.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | high | UNDER-SCOPE | D anti-regression | `plan-review.md` `## Step 1: Evidence and pre-review snapshot` items 1-6 ("Costlier error", "Git ref asymmetry"); spec `k3yx72` Section 4.3 table has no row for them | E-01 to E-11 moved every section except Step 1's evidence items, the core citation-disposition rule with its two measured precedents. The rewrite would silently drop them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-05 moves them verbatim into `r1-references.md`, the check whose job they are; V-05 greps for both precedents. |
| PR-002 | high | UNDER-SCOPE | D anti-regression | `plan-review.md` `### 0.1 Build the review-scope ledger`, `### 0.3 Discover the plan contract`, and `aw ipd lint --phase review-finalize` in `### Structural preflight`; E-11 kept only "pre-review commit" and "`aw ipd lint --phase author`, `aw ipd coverage`" | Spec 4.3 assigns these to the runner pre-pass, but an interactive `/plan-review` has no pre-pass. E-11 kept only part of them, so the scope ledger (which the mandated final enumeration depends on) and the finalize re-lint would be lost. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-11 keeps 0.1, 0.3, the pre-review commit and the whole structural preflight (except the two orchestrator subsections E-05 moves) verbatim; V-11 greps for each. |
| PR-003 | high | UNDER-SCOPE | C rollout | `runner_shared.build_review_prompt` sends `/plan-review <path>`; `kk62qt` E-04 `--review-mode single` "is the current `/plan-review`"; spec `k3yx72` 13.3 V2 | Once this plan merges, the single-turn runner review runs the new tiered checklist, and so does the pilot's "current" method. Unless the pre-change file is kept as a fixed baseline, the pilot compares the new review with itself, and nothing records the pre-change text for E-12's map. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | fixed | E-01 records the baseline commit and `aw check` line; E-12 writes the baseline into the README; the Scope states the behavior change; a Deferred row with `- Carrier: kk62qt` hands the pilot's use of the baseline to Order 09. |
| PR-004 | medium | IN-SCOPE | G sequencing | E-10 "`- Review-Depth: <tier>` is written here (... registered by Order 02)"; `- Item-Dependencies: none`; probe: a copy of this plan with `- Review-Depth: standard` lints `IPD-M103` today | If 01 merges before 02, every review instructed by `s7-finalize.md` writes a field the linter rejects as unknown. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | `- Item-Dependencies: executed:gv3smb`; orchestrator `tiwj2o` row 01, ordering note and E-01 edge updated to match (cross-plan). |
| PR-005 | medium | UNDER-SCOPE | D stale citations | `agent_workflows/review_findings.py` comments "because the shipped workflow table has it (plan-review.md:...)" and "`plan-review.md:...` says the history prose" | E-13 swept only `.aw/system/workflows`; two code comments cite moved text by line number and one `plan_readiness.py` comment names the moved section. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-13 also updates those comments (comment-only); Scope-Paths adds both modules; V-13 widens the `rg` to `agent_workflows`. |
| PR-006 | low | IN-SCOPE | E core-tier budget | `conftest.py` core-tier 30 s budget; measured scratch install 3.4 s; no other core test runs a full install | E-17 is a core module doing an install; four installs would take a noticeable share of the 30 s budget. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-17 uses one module-scoped install; V-17 pastes its duration. |
| PR-007 | low | IN-SCOPE | G spec trace | spec `k3yx72` dated 20261017 (post-cutover); `production_checks.spec_uncited_trace_ids('.', 'k3yx72')` lists `R1`..`R7` uncited | The checks R1 to R7 were cited unqualified, which SPEC-PLAN-TRACE ignores. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-05 to E-07 cite `` `k3yx72` R1 `` .. `` `k3yx72` R7 ``. |
| PR-008 | low | IN-SCOPE | G executability | E-11 tier list; spec `k3yx72` 5.1 "`orchestrator` ... Not rated by T" | E-11 lists `t-tier.md` for every review, but an orchestrator is not rated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-11 marks T as skipped for an orchestrator. |
| PR-009 | medium | UNDER-SCOPE | durable carrier | `aw commit` refusal `check.ipd-uncarried-obligation: ... deferred row 1, deferred row 2, deferred row 3 records an outstanding obligation with NO durable carrier` | Deferred rows 1-3 were prose only and would vanish from `aw attention` once this plan executes (post-cutover plan, so an error). | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Row 1 carries `gv3smb, uiyoax`; rows 2 and 3 carry `kk62qt`, whose E-09 files the Stage 2 backlog item. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should Step 1's evidence items go, given spec 4.3 maps them nowhere? | `r1-references.md` | `_kernel.md` (sent on every prompt, costing bytes on every step); spec amendment (out of this plan's authority; the spec's 4.3 promise "nothing is dropped" already requires keeping them) | spec `k3yx72` 4.2 row R1 ("locating each by symbol, heading, or quoted text"); 4.3 "Every part of it goes to exactly one place; nothing is dropped" | yes |
| D-2 | Should Order 01 depend on Order 02? | Yes, `executed:gv3smb` | Remove the `Review-Depth` write from E-10 and add it in Order 04 (moves a spec 7.2 S7 instruction away from the S7 step file) | probe of this plan with `- Review-Depth: standard` gives `IPD-M103`; `gv3smb` E-01 registers the field and has no dependency | yes |
| D-3 | Who keeps the pilot's "current `/plan-review`" baseline usable? | This plan records the commit; `kk62qt` uses it (Deferred row with Carrier) | Keep a copy of the old file in the shipped tree (it would ship a second, stale reviewer to every target repo) | spec `k3yx72` 13.3 V2 and the 13.3 line that each review runs "from the same commit"; `kk62qt` E-04 | yes |
| D-4 | Split E-03 on the `IPD-Z602` advisory? | No | Split into three E-items (they would edit one file in three passes) | E-03 names one deliverable, `p-proofread.md`; the clauses are its contents | yes |
