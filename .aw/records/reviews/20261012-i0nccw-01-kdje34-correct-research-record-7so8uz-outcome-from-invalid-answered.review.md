# Review findings: plan kdje34

- Subject-Id: kdje34
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `8a523e16e`. The pending plan matched the sealed lane input byte for byte and was already committed, so no snapshot commit was needed. `aw ipd lint --phase author` reported `clean`. `- Kind: child`.

Verified: `aw research index --check` exits 1 with exactly one `frontmatter-invalid` line for `7so8uz`. The record reads `outcome: answered` with `consumed-by: [0b7fic]`. Plan `0b7fic` is in `executed/`. `aw research set-outcome --help` restricts `--to` to the four-value vocabulary. Rehearsal (then reverted with `git checkout`): `--apply` produced a one-line diff, the check exited 0 with 0 `frontmatter-invalid` lines, `INDEX.json`/`INDEX.md` are gitignored (`.aw/.gitignore:50-51`), and `tests/test_research_index.py` reported `51 passed`. Backlog `i0nccw` carries `Blocks-Release: next`, which the plan inherits.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G (lifecycle gate) | `aw ipd lint --phase pre-transition` on the original plan: `check.ipd-uncarried-obligation: 3 obligation(s) name no durable carrier: deferred row 1, deferred row 2, deferred row 3` | The three deferred rows had no carrier, so the terminal transition would refuse after the work was done. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to each row. After the fix, pre-transition lint reports 0 uncarried obligations. |
| PR-002 | MEDIUM | IN-SCOPE | G (execution contract) | Original gate text "Move this plan to `.aw/records/plans/executed/` only after ..." | The gate told the executor to move the plan by hand. It had no scope fence, no hard rule to paste actual output, no staged-set check, and no runner/executor ownership of begin and finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate as an EXECUTION CONTRACT, a SCOPE FENCE (justify with `--scope-reason`, no stop directive), and a POST-GATE LIFECYCLE with conditional runner ownership. |
| PR-003 | LOW | IN-SCOPE | E (evidence feasibility) | E-01 "skip E-02"; V-02 demands `git show HEAD` | If the record was already fixed, E-02 would be skipped but could never reach `performed`, and V-02 would demand a commit that does not exist. A bare `HEAD` can also move before validation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now has a recorded no-op branch and records its commit hash. V-02 cites that hash and has an evidence path for the already-fixed case. |
| PR-004 | LOW | IN-SCOPE | Plan contract (OQ owner) | OQ-01 `- Owner: none` | The owner was wrong: the plan author resolved the question. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `plan author`. |
| PR-005 | LOW | IN-SCOPE | G (live counts) | Review run: 275 `dangling-citation` versus the plan's 274 | The count has drifted. It is context only and is not used as a bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F7 recording the re-measurement and the repeated rehearsal. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Carry the authoring-hardening deferral as backlog, or decline it? | Decline, with reason. | File a new backlog item now. | The backlog item scopes only the record fix. The existing gate caught the defect, and F6 found no recurrence. | yes |
| D-2 | `adopted` or `informational`? (confirming the author's OQ-01) | `adopted`. | `informational`. | Record `consumed-by: [0b7fic]`; `0b7fic` is executed. | yes |
