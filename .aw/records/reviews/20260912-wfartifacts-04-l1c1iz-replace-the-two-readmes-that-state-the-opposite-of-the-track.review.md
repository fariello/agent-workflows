# Review: replace the two READMEs that state the opposite of the tracking rule, child l1c1iz (Set wfartifacts)

- Subject-Id: l1c1iz
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `14b09376`. `aw ipd lint --phase author` CONFORMED with zero findings before semantic
review, and `--phase review-finalize` conformed after every revision.

SELF-REVIEW DISCLOSURE: the same agent and model authored this Set minutes earlier, so this is close to
a self-review and is worth less than an independent one. Its value therefore rests on what was
EXECUTED rather than reasoned: every numeric claim in every plan was re-measured against the
repository, which is what produced the findings below.

THIS CHILD WAS OVER-SCOPED AND THE REVIEW NARROWED IT, which is the most consequential change this
review made to the Set.

WHAT WAS CONFIRMED. `.aw/records/README.md` IS byte-identical to the workflow-artifacts README template
(verified by a Python `==` comparison, not by eye), and `records/reviews/` holds exactly 170 files, so
the wrong README really does describe a different tree with a different policy.

WHAT WAS REFUTED, AND IT RE-SCOPES THE PLAN. The plan treated this as a SHIPPED defect. It is not. The
shipped template `templates/agents-README.md` is already CORRECT ("# .aw/records/ / Agent tooling for
this repository", describing `plans/` and `workflows/` ownership), `engine.py:5205` emits it to
`.aw/records/README.md` on install, and a freshly installed scratch repo was confirmed to receive the
correct text. So only THIS checkout is wrong, from the Order 11 migration, and an executor following the
plan as written would have REPLACED CORRECT SHIPPED PROSE with a variant.

ALSO MEASURED: no test pins the content. Four assertions across `test_dir_readmes.py` (`:47`, `:68`,
`:72`) and `test_record_producers.py:364` check existence and path suffix only, so the plan's "a test may
pin this" caution is resolved to a definite no and E-03 should expect no test change.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-004 | HIGH | OVER-SCOPE | C. Architecture / F. Honest documentation | `templates/agents-README.md`; `engine.py:5205`; a fresh scratch install; the four test sites | THE PLAN WOULD HAVE EDITED CORRECT PROSE. It treated the wrong `.aw/records/README.md` as a shipped defect, but the shipped template is already right, is emitted on install, and a verified fresh install receives it. The defect is LOCAL DRIFT in this checkout only. Separately, the plan's caution that a test "may pin" the content resolves to NO: all four assertions check existence or path suffix. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Scope and Concern now state this is local drift, not shipped. E-03 re-titled to REPAIR this repo's file, told to start FROM the shipped template, and explicitly forbidden from editing it. V-03 requires `git diff --stat` proving the template UNCHANGED and treats a modified template as a FAILED validation. F-5 corrected to record that no assertion needs changing; F-6 added with the evidence. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Extend the shipped template to describe all the records trees, or leave it? | LEAVE IT, and let E-03 decide whether to EXTEND this repo's copy. | Extend the template to enumerate every records tree (rejected as scope creep discovered mid-review: the template is correct for what it claims, and widening it is a separate improvement that would need its own review); rewrite the template (rejected outright, PR-004). | The template's text; the fresh-install verification. | yes |
