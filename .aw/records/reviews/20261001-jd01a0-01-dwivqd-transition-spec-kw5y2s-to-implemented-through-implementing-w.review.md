# Review findings: plan dwivqd

- Subject-Id: dwivqd
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `5a2415e03`. The plan was committed and byte-identical to the lane input. `aw ipd lint
--phase author` was clean before review and `--phase review-finalize` clean after.

Re-measured at review:
- All six `wslayout` plans are in `executed/`; `xx5b7a` (the dependency) is in `executed/`.
- `SPEC_TRANSITIONS['approved']` = deferred/implementing/parked/reviewed/superseded; booleans `False True True`;
  authority `{'who': 'executor', 'by_human': False, 'human_token': False, 'evidence': True}`;
  `SPEC_TRANSITIONS['implemented']` = `['deferred', 'superseded']`.
- `_evidence_resolvable(<spec>, <rh5tt6 executed path>)` -> `True`; one-step dry run -> `aw specs set: illegal transition approved -> implemented`.
- Dry-run `--status implementing --graduated-to wslayout` -> `would move ... -> .../specs/implementing/...`.
- Census `11 12 ['records'] []`; `git check-ignore` matches `.aw/.gitignore:33/:34`; root `.gitignore` 0 layout hits.
- Scratch end-to-end (copied specs + executed plans, gitignored sidecar): both hops exit 0 with `--no-commit`;
  unstaged status ` D approved/...` + `?? implemented/...`, after `git add -A` a single `R`; final front matter
  `Status: implemented`, `Graduated-To: wslayout`.
- `offer_commit(repo, [old, vanished-intermediate, new])` -> `committed 2 path(s) ... (1 path(s) had nothing to commit)`, `R100 old new`.
- `aw attention --format json`: `valid False`, 14 violations (13 stranded lanes, one `89xjll` unsafe field), none naming kw5y2s; kw5y2s class `ready`.
- `aw specs check`: 1 pre-existing finding on `89xjll`.
- `rg -rn` in the plan is ripgrep's REPLACE mode (`-r n` replaced matches with `n`); `rg -n` shows 4 prose hits in 3 files, none resolving by directory.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Unsatisfiable bar | `aw attention --format json` `valid False`, 14 pre-existing violations | E-05, V-05 and stop condition 5 required `valid: true`. That was false before any edit, so the plan could never complete honestly. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bar is now an unchanged before/after violation set, none naming kw5y2s; do not clear others' violations. Added F-11. |
| PR-002 | MEDIUM | IN-SCOPE | E. Evidence command | plan E-06/V-06 `rg -rn "kw5y2s" tests/` | `-r` is ripgrep's replace flag, so the pasted output replaced every match with `n` and could not show what the hits cite. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Changed to `rg -n`. |
| PR-003 | MEDIUM | IN-SCOPE | G. Unsatisfiable bar | `aw specs check` -> 1 finding on `89xjll` | "`aw specs check` conforming" after each hop could not hold. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now "no new finding, none naming kw5y2s" against a pre-change run. |
| PR-004 | MEDIUM | IN-SCOPE | E. Evidence feasibility | scratch probe: unstaged move shows ` D` + `??` | V-03 demanded `git status --porcelain` show an `R`, which an unstaged move never shows. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 pastes the D/?? pair plus the Id; the rename is proven by the final commit's `R` line in V-05. |
| PR-005 | MEDIUM | UNDER-SCOPE | D. Irreversibility | `SPEC_TRANSITIONS['implemented']` = `['deferred','superseded']` | The plan did not say that E-04 cannot be undone through the tooling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Stated in E-04 and recorded as F-12. |
| PR-006 | LOW | IN-SCOPE | G. Commit path | `git_commit_helper.offer_commit` behavior probe | The plan left open whether each hop self-commits, which could double-commit or split the rename. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `--no-commit` on both hops and one `aw commit` at the end. Verified that the vanished intermediate path is tolerated. Gate now names begin/finalize ownership and the `--scope-ack`. |
| PR-007 | LOW | IN-SCOPE | G. Stale premise | `.aw/records/plans/executed/...xx5b7a...` | The dependency was pending at authoring and is now satisfied. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Stop condition 3 annotated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Bar for a dirty attention view | Unchanged before/after violation set | Require `valid: true` (unsatisfiable); drop the check | measured 14 pre-existing violations | yes |
| D-2 | Commit surface | `--no-commit` per hop, one `aw commit` | Setter `--commit` per hop (two commits, split rename) | offer_commit probe; AGENTS.md `aw commit` mandate | yes |
| D-3 | Keep OQ-01 resolved (agent may transition on backlog instruction) | Keep as authored | Escalate to blocking | backlog `jd01a0` WHAT TO DO; `->implemented` `by_human: False`. The transition is one-way (F-12), but plan approval by a human is still required before execution, so the irreversible act is human-gated; maintainer told 2026-10-02 in this review's final report | no |
