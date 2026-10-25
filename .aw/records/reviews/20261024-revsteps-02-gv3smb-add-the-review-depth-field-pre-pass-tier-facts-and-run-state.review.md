# Review findings: plan gv3smb

- Subject-Id: gv3smb
- Subject-Type: ipd
- Reviewed-At: 2026-10-25
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ebfdfc561` in a runner lane worktree (non-interactive). The lane-input copy is
byte-identical to the tracked plan (committed, unmodified, `f10f8f3cd`), so no pre-review snapshot.
`aw ipd lint --phase author` and `--phase review-finalize` are clean before and after; the remaining
`IPD-Z602` info on E-04 is three parsers of one reply/record grammar in one new module, judged not a
split (D-3).

Verified: `ipd_schema.META_ATTENDED`, `META_RECOGNIZED`, `size_warning`, `MAX_TASK_GROUPS = 5`,
`MAX_E_LEAVES = 18` exist as cited. `ipd_lint.ParsedDoc.exec_task_groups` and `exec_leaves` exist, and
`ipd_lint.parse('')` returns `meta_fields={}`, 0 task groups, 0 leaves without raising.
`ipd_lifecycle.frozen_region_digest` exists. `run_dashboard.collect_rows`, `COLUMNS`,
`ATTEMPT_FACT_FIELDS`, `ATTEMPT_FACTS_SCHEMA_VERSION = 3`, and `run_analytics_attempts.ATTEMPT_FILTER_FIELDS`/
`ATTEMPT_GROUP_FIELDS` exist with `readiness` present (the `avg8qv` precedent). `aw runs query schema
--json` exposes `data.payload.attempt_grain.filter_fields` and `group_by_fields`, so V-06 is reachable.
`docs/run-analytics.md` has "Review cost: per-attempt analysis" and "What is not recorded yet".
`runner_shared.add_run_label_flags` help says `--review-variant` is "no behavior change" (F-03). Spec
`20260802-1904` Section 4.4 exists with an `Attended` paragraph to imitate. `uiyoax` E-03 and E-06 call
`parse_tier_marker`, `parse_tier_answers`, `tier_answers_complete`, `tier_facts` and
`record_review_tier`, matching the names here. A scratch copy of `3bwrfx` carrying
`- Review-Depth: standard` lints `IPD-M103` today (F-02 confirmed).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | medium | IN-SCOPE | G executability | `agent_workflows/ipd_schema.py` `validate_metadata` holds "attended = fields.get(META_ATTENDED)"; `parse_metadata_block` only appends "duplicate field" / "unknown field" | E-01 put the enum check in `parse_metadata_block` "the pattern the `attended` check uses", but that check lives in `validate_metadata`. An executor following the text would mis-place it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 names `validate_metadata` and `ipd_lint.check_metadata`; V-01 demands lint output on a valid and an invalid scratch copy. |
| PR-002 | medium | UNDER-SCOPE | C canonical mechanism | executed `avg8qv` E-04 edits `run_dashboard_assets/dashboard.js` (`DIMS`, `FACETS`, `GROUPABLE`); `collect_rows` has two attempt `base` dicts (recorded and synthesized) | E-06 claimed to follow `avg8qv` "exactly" but omitted the dashboard UI and named one row dict, so the tier would be queryable by CLI but invisible on the dashboard, and synthesized rows would lack the key. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-06 adds both `base` dicts and the four `dashboard.js` lists; Scope-Paths adds `dashboard.js`; V-06 demands those hunks. |
| PR-003 | low | IN-SCOPE | A data integrity | E-05 "writes `attempt[\"review_tier\"]` (the tier or `None`)" | The recorder accepted any string, so a caller bug could record a tier the plan field refuses, polluting the analytics groups. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Tier must be in `REVIEW_DEPTH_VALUES` or `None`, source in the three named values, else `ValueError`; test (f) covers it. |
| PR-004 | low | IN-SCOPE | correctness | spec `k3yx72` Section 8.1 rule 2 "Leading and trailing whitespace is ignored ... A trailing code fence line is ignored" | E-04's order "stripping surrounding whitespace and ignoring a trailing code-fence line" was ambiguous about which text is stripped. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Reworded: drop the trailing fence line, then strip the last line. |
| PR-005 | low | UNDER-SCOPE | E testing | E-07 (g) asserted only the `simple` group; `avg8qv` E-05 extended `_review_run` in `tests/test_run_analytics_review_cost.py` | The test did not prove a missing key lands in the empty group, and the fixture file it must extend was not in Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | (g) also asserts the empty group; (h) covers empty input to `tier_facts`; Scope-Paths adds the test file. |
| PR-006 | low | IN-SCOPE | E evidence | E-03 expected outcome "(it returns `None` values instead)"; measured `ipd_lint.parse('')` returns counts of 0 | The outcome claimed `None` for counts that the parser it builds on returns as 0. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Outcome states 0 counts and `None` for `kind`/`scope_paths`. E-04's outcome made concrete too. |
| PR-007 | low | IN-SCOPE | G spec trace / Section 12 | spec `k3yx72` is post-cutover; Section 12 "the implementing plans must declare which format they target" | MD-1 was cited unqualified, AC-08 not at all, and the storage format was not declared. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Qualified `k3yx72` MD-1 / AC-08 citations in E-04 and E-05; Scope check declares front-matter storage. |
| PR-008 | low | IN-SCOPE | R7 cross-plan | E-04 parses answers as lines "starting with `1.` to `5.`"; `3bwrfx` E-04 said only "answer each on one line" | The step file that instructs the agent did not name the line form the parser reads, so the T postcondition could fail on well-meant answers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | `3bwrfx` E-04 now names the `1.` to `5.` form (re-scope history line added there). |
| PR-009 | low | UNDER-SCOPE | durable carrier | `check.ipd-uncarried-obligation` fired on the same prose-only Deferred shape in `tiwj2o` and `3bwrfx` this run | Both Deferred rows lacked a typed carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Row 1 `- Carrier: uiyoax`; row 2 `- Carrier-Declined:` (owed by the `4sd62s` migration per `k3yx72` Section 12). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the recorder reject an unknown tier? | Yes, `ValueError` | Record as-is (silently pollutes groups); coerce to `None` (hides the caller bug) | spec `k3yx72` MD-1 forbids changing the agent's tier, which rejection does not do; the plan field is a closed enum (E-01) | yes |
| D-2 | Include the dashboard UI? | Yes | CLI only (the stated precedent `avg8qv` E-04 edited the UI, and a hidden dimension is the silent-failure case rubric F names) | executed plan `avg8qv` E-04 | yes |
| D-3 | Split E-04 on `IPD-Z602`? | No | Split marker and answers parsers (two passes over one small grammar in one module) | E-04 is one module's parsing surface; V-04 already tests it as one `-k "marker or answers"` selection | yes |
