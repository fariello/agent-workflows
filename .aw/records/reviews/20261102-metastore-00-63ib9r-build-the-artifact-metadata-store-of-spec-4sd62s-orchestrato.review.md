# Review findings: plan 63ib9r

- Subject-Id: 63ib9r
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `949d698c3` in a non-interactive runner review-sweep lane worktree. The lane-input copy (revision 3) was byte-identical to the tracked plan, which was committed and unmodified, so no pre-review snapshot was needed. `aw ipd lint --phase author` and `aw ipd coverage 63ib9r` were clean before the edits. After the edits, `--phase review-finalize` reported `IPD-S408`, because the text had changed and the coverage fingerprint was stale. Coverage repair attempt 1 re-ran `aw ipd coverage 63ib9r`, which reported "ready for review" and recorded the new fingerprint `96fe24cd857b`; lint was then clean. Rows: 13 -> 13, so no row was deleted.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Child table rows 10 and 11; E-10, E-11 | Dependencies missing `xexn45` (row 10) and `1ajqaa`, `dcerjg` (row 11) | Match each child's `- Item-Dependencies:` | PR-001. |
| Completion criteria, writers and cutover lines | Omitted the phase-B AC-3 and AC-6, and the real AC-1 and AC-30(2) | Added, matching `xexn45` and `cxxmyv` | PR-002. |
| OQ-01 | `Owner: none`; split decision pending child reviews | `Owner: plan author`; both child reviews declined the split | PR-003. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step R1

- Checked: every child file name in the table exists under `pending/`; each child's `- Item-Dependencies:` value; the AC ownership sections of `xexn45`, `1ajqaa`, `59aiyh` and `cxxmyv`; the review records of `tve77h` and `dcerjg` for the split decision; spec `4sd62s` section 7 steps 1 to 9 against the Scope check; `runner_shared` `_freeze_attended_hold` for the `not-run` claim about Order 13 under an unattended run.
- Rows 10 and 11 disagreed with the children (PR-001). `59aiyh` declares `executed:tve77h, executed:xexn45`. `9o83cr` declares `executed:ffceq0, executed:t4gl15, executed:59aiyh, executed:1ajqaa, executed:dcerjg`.
- The paragraph under the table says an unattended run holds Order 13 `not-run`. `runner_shared._freeze_attended_hold` sets `q_entry["status"] = "not-run"`, which matches.

### Step R2

- Checked: the E/V bijection is 13/13; each `V-*` demands pasted `aw find plans <id6>` output, which is reachable by construction.
- E-items now mirror the corrected child dependencies.
- The checklist is orchestration only. It holds no work that a child does not cover, and `aw ipd coverage` agrees.
- Gate: it includes the human-approval rule, the pasted-output rule, conditional finalize ownership (the runner retires the plan, or a hand run uses `aw ipd finalize`), a path-scoped `aw commit` and no push. It has no hand `git mv`.
- `IPD-S407`: none reported. `IPD-S408`: repaired in attempt 1 (see the round preamble).

### Step R7

- Checked the whole Set. Every step of spec section 7 has exactly one owner. The `Carrier:` rows across the children close on a sibling or on `nq1src`/`f4p4vn`. `cxxmyv`'s reviewed scope matches its row 13.
- The phase-B AC-3 and AC-6 forms belong to `xexn45` (its AC table: "`cxxmyv` re-demonstrates on logs"), and the completion criteria omitted them (PR-002).
- `cxxmyv`'s review (round 1) added AC-1 and AC-30(2) to its real-repository list, so the cutover criterion is updated to match.

### Step S5

- Checked: OQ-01 is a reviewer-and-author decision, not the maintainer's. Both child reviews have since declined the split (`tve77h` D-1, `dcerjg` D-2), so the resolution stands. No question needs the human.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | R7 / child table | `59aiyh` "- Item-Dependencies: executed:tve77h, executed:xexn45"; `9o83cr` "- Item-Dependencies: executed:ffceq0, executed:t4gl15, executed:59aiyh, executed:1ajqaa, executed:dcerjg" | Rows 10 and 11 and E-10/E-11 understated the children's dependencies, so a hand executor following table order could run `59aiyh` before `xexn45`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rows and E-item `Depends on` now match the children. |
| PR-002 | LOW | IN-SCOPE | R7 / completion criteria | `xexn45` AC table rows AC-3 and AC-6; `cxxmyv` "Owns, finally on the real repository ... AC-1 ... AC-30 cases 2 and 3" | The criteria omitted ACs the children own. | Overall:Low | FIXED | Added. |
| PR-003 | LOW | IN-SCOPE | S5 owner rule | OQ-01 "- Owner: none"; `tve77h` review D-1; `dcerjg` review D-2 | The owner field did not name who decided, and the deferred check is now complete. | Overall:Low | FIXED | `Owner: plan author`; resolution cites both review decisions. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which source is authoritative for a child's dependencies, the table or the child? | The child's `- Item-Dependencies:` (what the runner reads) | Edit the children to match the table | `runner_shared` dependency checks read the child's field | yes |
