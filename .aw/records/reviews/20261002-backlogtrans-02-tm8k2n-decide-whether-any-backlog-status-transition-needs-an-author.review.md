# Review findings: plan tm8k2n

- Subject-Id: tm8k2n
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032734Z-4093657` at HEAD `382e2622e`. The plan was
committed and byte-identical to the sealed lane input (rev-8), so no snapshot was needed. `- Kind: child`, so
`IPD-S407`/`IPD-S408` do not apply. `aw ipd lint --phase author --agent` was clean before review.

Re-measured in a throwaway repo under `/tmp/opencode/` (no tracked record touched):
- F-01: `aw backlog set open <id> --by-human` and `aw backlog set <id> --status open --by-human` both exit 2 with
  `unrecognized arguments: --by-human`.
- F-07: `done -> open` exits 0 and relocates on both spellings, with or without `--allow-terminal-reopen`.
- F-04: the runner's argv sites are present (`--status graduated` handoff, `--status open` rollback with
  "handoff incomplete", `close_backlog_item` with `--status done --evidence`), and `close_backlog_item` is reached from
  both hosts.
- F-05: the `promote_question_to_backlog` `item.status = "blocked"` creation and the enqueue comment are present.
- Dependency `cc2m29` is `executed`, and backlog `qbn1dx` exists (`graduated`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A correctness / honest documentation | plan F-08 "ungated but NOT unattributed"; E-05 "the history actor string that attributes every move"; `backlog.py` `actor="aw backlog"` at its three history writers; probe history `- 2026-10-07 open (aw set): probe reopen positional` | The actor parenthetical is a TOOL label, not the mover. So a terminal reopen is ungated AND unattributed. The plan's fourth reason for declining the reopen gate, and the README text E-05 would publish, overstate the control. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11 and a correction note on F-08. The sweep covered E-01(c), E-04 (honest residual), E-05 and V-05 (describe it as a record, not as attribution), the OQ-01 review note, and Proposed change 1. The recommendation still stands on reasons (1) to (3). |
| PR-002 | MEDIUM | IN-SCOPE | C duplicate path / evidence drift | `.aw/records/backlog/README.md` `## Legal status transitions` / `### Reopen policy`; `attention_contract.BACKLOG_TRANSITIONS` now present; plan F-02 "`hasattr(attention_contract, "BACKLOG_TRANSITIONS")` is `False`" | `cc2m29` has landed. It already documents the reopen allowance and ships the legality table. E-05 as written would add a second reopen statement, and F-02 is stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12. E-05 now extends `cc2m29`'s `### Reopen policy` and does not restate it, and it names the legality table as a control. |
| PR-003 | MEDIUM | IN-SCOPE | G execution contract | gate "Do not claim done and do not move this plan to `.aw/records/plans/executed/` until"; "a diff touching `agent_workflows/` is a signal to stop" | The gate had no conditional runner/executor finalize ownership and no scope-reconciliation wording. The stop instruction was framed as a scope stop. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added runner-owned finalize under the runners, `aw ipd finalize` by hand, and the `--scope-reason`/`--scope-ack` fence. A production diff is now reported against OQ-01 as a failed premise. |
| PR-004 | LOW | IN-SCOPE | E testing / feasibility | V-03(b) "the probe shown installed WITHOUT modifying a tracked file" | The plan named no mechanism for a probe that changes behavior without editing a tracked file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03(b) now names the `cc2m29` F-07 method: an in-process `-p` pytest plugin under the gitignored `tmp/`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does PR-001's correction undermine OQ-01 enough that it should be reopened as blocking? | No. OQ-01 stays resolved as a recommendation, with a review note so the maintainer weighs it on the corrected fact at approval | Reopen OQ-01 as `Blocking: yes` (would block a plan whose deliverable is the recorded answer, and approval is already the attestation per the plan's gate) | plan OQ-01 reasons (1)-(3) and F-09 price unaffected by F-11; plan gate "Approving it therefore means accepting the recommendation in OQ-01" | yes |
