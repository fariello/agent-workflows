# Review: rewrite the 86 stale workflow-artifacts references in the shipped bodies, child 9x1rps (Set wfartifacts)

- Subject-Id: 9x1rps
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

THE CENTRAL ACT OF THIS REVIEW LANDED HERE: the plan's own counts were re-measured rather than trusted,
and two of them were wrong. The 86 occurrences and the 0 prefixed re-verified EXACTLY, but the file
count and two per-file figures did not.

BOTH ERRORS WERE MINE AT AUTHORING AND BOTH WOULD HAVE MISLED THE SWEEP. Counting files with `grep -rl`
and no `--include` pulled in three `__pycache__/*.pyc` binaries (27 claimed, 25 real, 28 unfiltered);
compiled caches are build output and cannot be edited. And two per-file figures were LINE counts from
`grep -c` sitting in a table whose aggregate was OCCURRENCES from `grep -o`, so a sweep driven by those
numbers would have declared itself complete with three references still in the tree.

THE FALSE CLAIMS THIS PLAN REPAIRS WERE CONFIRMED VERBATIM. `assess.md:139` reads "The run record in
`workflow-artifacts/` is local-only working material" and `:189` reads "It is gitignored by default; do
not commit or force-add it." Neither is true in a target repo today, which is precisely why this child
must not land before Order 02.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Testing / F. Honest documentation | both greps run with and without `--include`, and with `-c` vs `-o`, at review | TWO INDEPENDENT COUNTING ERRORS. (a) The FILE count was 27 and is 25, because `grep -rl` without `--include` matched three `assess/tools/__pycache__/scan_secrets.cpython-3*.pyc` binaries; the unfiltered total is 28. (b) Two per-file figures were LINE counts (`00-run-protocol.md` 18, `README.md` 11) inside a table whose aggregate 86 was OCCURRENCES; the true occurrence counts are 20 and 12. A line-driven sweep leaves 3 references behind while reporting success. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern corrected to 25 SOURCE files with the `__pycache__` cause stated; the heaviest-file figures corrected to 20 and 12 with the unit error named as F-8; E-01 now MANDATES `-o` plus `--include` and carries a full re-measured per-file enumeration; V-01 makes a pasted `grep -c` or an unfiltered command a FAILED validation regardless of its number. Added F-7 and F-8. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Occurrences or lines as the unit for this plan? | OCCURRENCES, stated explicitly wherever a count appears. | Lines (rejected: two references on one line are two rewrites, so lines under-report the work and the aggregate 86 was already occurrences; mixing the two is what produced PR-001). | `grep -c` vs `grep -o` measured on both heaviest files. | yes |
| D-2 | Should the `__pycache__` files be counted, since they DO contain the string? | NO. | Count them (rejected: they are build output, are not editable, are regenerated from `scan_secrets.py` which IS in scope, and including them overstates the surface by three files). | The unfiltered vs filtered grep difference. | yes |
