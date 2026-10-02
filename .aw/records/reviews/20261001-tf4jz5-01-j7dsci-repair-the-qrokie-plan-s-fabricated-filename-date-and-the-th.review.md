# Review findings: plan j7dsci

- Subject-Id: j7dsci
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `6830882b5` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review and `--phase review-finalize` clean after revision.

Re-verified (read-only; the rename route was driven in a throwaway git repo under `/tmp/opencode/` seeded with the
real target file, so no repository file was modified):
- Target still at `executed/20260101-instsafe-07-qrokie-...ipd.md`, `- Date: 2026-07-23 (fleshed 2026-07-26 from
  research)`, `- Id: qrokie`, `- Set: instsafe (install safety and ownership)`, `- Order: 7`; its history carries
  "2026-07-26 fleshed to a design spec from research".
- `949enf` (executed 2026-10-01), `fqcax0` (executed), `rlcq7g` (executed) have all landed since authoring.
  `5h8u3z` is now in `backlog/done/`, `mt6j1p` in `backlog/graduated/`; two declared Scope-Paths no longer exist.
- `plans_refs._preserved_date` reads the clustered filename date first. Throwaway repo:
  `group plans qrokie --set instsafe --rename --order 7` -> only `would set Set=instsafe Order=07`, both before AND
  after correcting `- Date:`; `rename plans --id qrokie --set instsafe --order 7` and `--slug ...` likewise. No
  `--date` flag on either plans verb.
- `plan_reference_rewrites_with_warnings` on the exact old/new pair: 20 edits over 10 files, 0 warnings
  (`tk1gqo`, `5h8u3z`, `jhrao5`, `tf4jz5`, `mt6j1p`, executed `949enf` and `fqcax0`, pending `6i8knl`, pending
  `wyk11f`, and this plan).
- `tests/fixtures/derive_plan_status_baseline.json`: dict of 732, keyed by id6, `"qrokie": "executed"`.
- `git grep -c '20260101-instsafe-07-qrokie'`: 48 occurrences across 23 files.
- `artifact_refs.dead_filename_citations(Path('.'), 'plans')` already reports old-name citations (e.g. `xp6o3v`,
  `STATUS.md`), so it is a usable post-rename census.
- `artifact_refs.apply_reference_rewrites(edits)` takes an explicit edit list, so a KEEP-only apply is possible.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Executability | `plans_refs._preserved_date`; throwaway-repo runs above | E-02..E-04 rest on F-04 ("correct the Date and `group --rename` works"). `949enf` has executed, so the verb previews no rename even after the fix; the plan as written cannot be executed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Route switched to OQ-03's own pre-authorized fallback: `git mv` + `artifact_refs.plan_reference_rewrites_with_warnings`/`apply_reference_rewrites`. E-02 re-justified (renamed name and parsed Date must agree), E-03/E-04 rewritten, F-04/F-05 annotated, F-11 added, OQ-03 updated. |
| PR-002 | HIGH | IN-SCOPE | A. Record integrity | rewrite set above; AGENTS.md executed-plan rule | The rewrite set is now 10 files, including EXECUTED `949enf` and `fqcax0`, whose findings must not be edited. The authored KEEP set (`5h8u3z`, `mt6j1p` as KEEP) and LEAVE set (`949enf`, `fqcax0` as pending) no longer match reality. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 re-classifies: KEEP `tk1gqo`; LEAVE everything else, with reasons. E-04 applies ONLY the KEEP edits, so no LEAVE file is touched and the restore step disappears. Gate forbids editing any executed plan other than the target's Date line. |
| PR-003 | MEDIUM | OVER-SCOPE | G. Stale premise | fixture keyed by id6 | E-06 re-keys a path entry that no longer exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now confirms no edit; fixture removed from Scope-Paths; V-06 proves `Compared N` unchanged. |
| PR-004 | MEDIUM | IN-SCOPE | G. Scope declaration | Scope-Paths | Two declared backlog paths have moved, and the new target path was undeclared. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope-Paths now: old and new target paths, `tk1gqo`, the three facet-less citers. |
| PR-005 | LOW | IN-SCOPE | G. Live-artifact criterion | E-01/V-01 "31 occurrences across 20 files" | Live counts used as bars; they are 48/23 now. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Counts are context re-derived at execution; `dead_filename_citations` added as a census instrument. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | Gate "before `aw ipd finalize` moves this plan" | Finalize ownership was unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Runner owns finalize under `aw oc run`/`aw agy run`; a hand executor runs `aw ipd finalize`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which route performs the rename now that no verb does? | `git mv` + the shipped `artifact_refs` rewriter, KEEP edits only | Add `--date` to the plans verbs (code change, out of scope); retire the plan as no longer executable | Plan OQ-03 pre-authorizes this fallback; F-03 hook measurement; `apply_reference_rewrites` accepts an explicit edit list | yes |
| D-2 | Are executed `949enf`/`fqcax0` LEAVE? | Yes | KEEP (rewrite their findings) | AGENTS.md forbids changing what an executed plan records; both cite the old name as the measured defect | yes |
| D-3 | Is the repair still worth doing (OQ-01)? | Yes, unchanged | Leave the wrong name | The pending `wyk11f` filename/Date mismatch rule makes an agreeing name and Date more valuable, not less | yes |
