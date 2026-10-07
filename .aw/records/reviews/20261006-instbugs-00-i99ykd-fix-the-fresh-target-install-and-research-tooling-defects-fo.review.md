# Review findings: plan i99ykd

- Subject-Id: i99ykd
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fe2ee961c` in an isolated review-sweep lane. Orchestrator (own first `- Kind:` bullet reads
`orchestrator`). Plan committed and byte-identical to the lane input, so no pre-review snapshot.
`aw ipd lint --phase author --agent` clean before semantic review; `aw ipd coverage i99ykd` ready.

Verified:
- All eleven children present in `pending/`; each child's `- Order:`, `- Kind: child` and `- Item-Dependencies:` match
  the `## Child IPDs` table (e.g. `pfub72` `executed:gi1w75`, `ka0g86` `executed:xzlu9b, executed:jbnkkh`, `kck7a5`
  `executed:whz0oi, executed:gzsfqn, executed:ka0g86, executed:okw4ke, executed:ic4eg0, executed:zye6k4`).
- Triage spot checks at HEAD: `.aw/system/VERSION` = `1.2.1` (D01); `agent_workflows/install_wizard.py:426`
  `f"{repo_formatted}/.aw/{cls}"` (D04); `install_wizard.py:955` `"installed_version": "2026.8.10"` (N2);
  `.aw/.gitignore:28` `/inbox/` and `:62` `/state/` (D14/D15/D02); `research_cmd._next_order_for_set` returns 0 for a new
  set (`agent_workflows/research_cmd.py:121-131`, D12). `kck7a5` E-items pin D02 and D06 as the Deferred row claims.
  Research `l6cbbb` and backlog `bh1cy5` (open, feature) exist.
- `check_engine.check_durable_carrier` on the unrevised plan: `error 1 obligation(s) name no durable carrier: deferred
  row 3: malformed `Carrier` reference(s) 'none (the table is in this plan)'`.

### Orchestrator coverage repair loop (IPD-S408)

- Attempt 1: after adding a Cross-IPD row assigning the children's missing `Blocks-Release` to "each child's own
  review", `aw ipd coverage i99ykd` reported `coverage-fail ... uncovered obligation: This orchestrator now carries ...
  each bug child must gain it too ...`. Change: row removed; observation moved to Scope check.
- Attempt 2: `aw ipd coverage i99ykd --no-commit` reported `coverage-fail ... uncovered obligation: At review the ten
  `- Work-Kind: bug` children carry no `- Blocks-Release:` ...`. Change: observation removed from the plan entirely and
  kept in this record (below). Re-run: `Orchestrator i99ykd is ready for review.`, `- Coverage: pass`, fingerprint
  `5891d6bc5dee...`; `aw ipd lint --phase review-finalize` clean. Checklist rows: 11 -> 11 (no deletion).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Project rule (durable carrier, I-07) | `check_engine.check_durable_carrier` output above; rule `check.ipd-uncarried-obligation` severity `error` (`agent_workflows/check_engine.py:695`) | Deferred row 3 wrote `Carrier: none (the table is in this plan)`, which parses as a malformed carrier id6 and fails `aw check` at `error`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with `Carrier-Declined:` stating the triage is the Findings table; `check_durable_carrier` now returns nothing for this plan. |
| PR-002 | HIGH | UNDER-SCOPE | Project rule (Every live bug gates the next release) | `AGENTS.md:164` "a spec or plan has no exemption field today and so must carry the gate"; `grep -c Blocks-Release` = 0 on all twelve instbugs plans | This `- Work-Kind: bug` orchestrator and ten bug children carry no `- Blocks-Release:`, so the Set's live bugs do not gate release `next` (`f33nrj`, planned). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Blocks-Release: next` added to this plan (the subject of this finding). The ten children (`whz0oi`, `gi1w75`, `pfub72`, `gzsfqn`, `xzlu9b`, `jbnkkh`, `ka0g86`, `okw4ke`, `ic4eg0`, `zye6k4`) are outside this review's ledger, so this was REPORTED to the maintainer rather than edited; set it with `aw ipd set <status> <id6> --blocks-release next` when each child is reviewed. |
| PR-003 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked a resolved-OQ statement, the pasted-output honesty rule, scope fence as declaration, and conditional retirement/finalize ownership for runner vs hand execution. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate amended. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the review edit the ten children to add `Blocks-Release`? | No; gate this plan, report the children to the maintainer | Edit all ten children in this review | plan-review Step 0.1 ledger is the named plan only; the coverage gate refuses parent text implying child work | yes |
| D-2 | Is the deferred triage-report row an obligation needing a carrier? | No; `Carrier-Declined` | File a backlog item for the triage report | The Findings table is the deliverable `l6cbbb` step 5 asked for | yes |
