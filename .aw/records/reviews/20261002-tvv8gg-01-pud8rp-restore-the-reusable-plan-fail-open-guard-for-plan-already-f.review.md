# Review findings: plan pud8rp

- Subject-Id: pud8rp
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032752Z-4094028` at HEAD `ca03f0c56`. The plan was
committed (`09dbc0975`) and byte-identical to the sealed lane input (rev-5); no snapshot needed. `- Kind: child`, so
`IPD-S407`/`IPD-S408` do not apply. `aw ipd lint --phase author` clean before review.

Re-measured: `tests/test_finidem_double_finalize.py` absent; `git grep` finds exactly two citations
(`agent_workflows/ipd_lifecycle.py` docstring of `plan_already_finalized` and the `#:` comment above
`FINDING_RECEIPT_NEVER_ISSUED`); `plan_already_finalized` contains `if bucket != "executed":`;
`TERMINAL_DIRECTORY_SEGMENTS` contains `/reusable/` and `_IPD_ACTIONS["reusable"]` is `ACTION_EXECUTE`; deletion by
`19313eed7` (2026-09-24 size trim); the deleted file's `ReusablePlanIsNotAlreadyFinalized` was behavioral; no
surviving test combines reusable with finalize (only `tests/test_ipd_lifecycle_cli.py` uses the finding constants,
for pending/executed/stale cases). An in-process scratch-repo probe (no file mutated) reproduced F-04: baseline
precheck `(1, receipt-never-issued)`, `finalize_outcome` 1 for the reusable plan and 0 for an `executed/` plan; with
the substitution monkeypatched, precheck `(1, receipt-consumed-already-finalized)` and `finalize_outcome` 0.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E testing / vacuous pass | `runner_shared.finalize_already_done` "if not plan_path.is_file(): return False" and containment check; plan E-04 "returns a NONZERO exit code" | The driver-seam nonzero assertion can pass vacuously if `finalize_already_done` rejects the fixture path for an unrelated reason (existence/containment guards from `1fzist`); E-03 guards vacuity for the predicate but E-04 did not for the seam. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04/V-04 add an `executed/` positive contrast (`finalize_already_done` True, `finalize_outcome` 0) and require both paths under the scratch root passed as `repo`. |
| PR-002 | MEDIUM | IN-SCOPE | G execution contract | plan gate "complete the terminal transition with the tooled lifecycle (`aw ipd finalize`)" | Unconditional finalize instruction; the runner owns the transition in a managed lane. Scope-fence declaration and backlog close step also absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: runner-owned in a lane, `aw ipd finalize pud8rp ... --apply` only by hand; scope fence as declaration with `--scope-reason`; `tvv8gg` closed after execution with `--evidence`. |
| PR-003 | LOW | IN-SCOPE | G executability | `grep -rn test_finidem_double_finalize agent_workflows/` also prints `binary file matches` for `agent_workflows/__pycache__/ipd_lifecycle.cpython-314.pyc`; E-05 left the mutation text implicit | E-01's "exactly TWO" count and V-06's "returning nothing (exit 1)" are unreliable with `grep -rn` while a stale `.pyc` exists; the mutation line was unspecified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and V-06 use `git grep`; E-05 names the exact replacement line. |
| PR-004 | LOW | IN-SCOPE | evidence accuracy | `git log -1 --format=%ad 80db6750c` -> "Wed Sep 23 21:17:33 2026" | F-05 dated the P16 purge 2026-09-22. Conclusion unaffected. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 corrected to 2026-09-23. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to make the driver-seam assertion non-vacuous? | Add an `executed/` positive contrast in the same test | rely on E-03's predicate contrast only (does not cover `finalize_already_done` guards) | `runner_shared.finalize_already_done` existence/containment guards; scratch probe outcome 0 for executed | yes |
| D-2 | Citation search command | `git grep` over tracked files | `grep -rn --exclude-dir=__pycache__` (works but easier to get wrong) | observed `.pyc` binary match at review HEAD | yes |
