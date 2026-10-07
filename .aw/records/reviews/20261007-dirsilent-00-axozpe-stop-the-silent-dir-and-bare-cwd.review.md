# Review findings: plan axozpe

- Subject-Id: axozpe
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T165339Z-456282` at HEAD `ad22ff70a`. The plan was
committed and byte-identical to the sealed lane input rev-1 (sha256 `9ecd5ba2...f9fe` matches); no snapshot needed.
`- Kind: orchestrator`. `aw ipd lint --phase author` was clean before review. After review, `review-finalize` reports
only `IPD-Q501` (blocking OQ-03, intended) and `IPD-S408` (coverage).

Re-measured in this worktree, which is itself an AW project (a scratch `/tmp` fixture was refused by the lane sandbox):
the six `Path(getattr(args, "dir", None) or os.getcwd())` sites resolve to `cli._run_record_history`, `_run_graduation`,
`_run_find`, `_run_search`, `_run_check` and `doctor.run`. `aw check specs` reports `21 specs checked` at the root and
`0 specs checked` from `docs/`. `aw specs check --dir docs --agent` emits `outcome:clean, exit 0, verified:true,
checked:0`. `aw doctor` from `docs/` reports `not installed ... [not-installed]`. The `resolve_verb_repo_root` grep
gives 91 lines across 25 modules, matching the child's figure. The children's ids, Orders, `Item-Dependencies`,
`From-Backlog: rgl2d4` and `Blocks-Release: next` all match the child table.

IPD-S408 bounded loop: attempt 1 ran `aw ipd coverage axozpe` after the revisions. It reported two `coverage-fail`
quotes, both naming the PR-001 gap (the criterion 1 note and the Under-scope line). Nothing changed after that: the
only remedies are to add a child or assign the work to an existing child, which is the maintainer's scope decision
(OQ-03). Attempt 2 was not spent, because no in-review edit can honestly resolve the gap. Per R6, the plan stays
`to-review` and `- Readiness:` stays absent.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A correctness / coverage | `agent_workflows/cli.py` `_nv_backend_args` "`sub.dir = getattr(args, "dir", None) or os.getcwd()`"; plan Deferred row "Carrier: rlhmt9" | A seventh, differently-spelled resolver bypass turns a bare call into an explicit `--dir <cwd>` for every noun-verb backend. Reproduced: `aw index research --check --agent` gives `findings, exit 1, 179` at the root and `conforms, exit 0, verified:true, 2` from `docs/`. No child covers it, and the Deferred row's carrier `rlhmt9` contains no bypass audit, so the handoff claim was false. | C:Medium; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | OPEN | The false carrier claim was corrected to `Carrier-Declined` pending OQ-03. Escalated as blocking OQ-03 (Finding: PR-001). The site also feeds write verbs (`group`/`rename`/`archive`), so assigning it is a scope and risk decision for the maintainer. |
| PR-002 | MEDIUM | IN-SCOPE | G executability / reachability | plan Required tests "which Order 04 carries as the last child"; `rlhmt9` V-01..V-05 carry no cross-child matrix | The plan claimed Order 04 performs a full cross-child before/after matrix, but `rlhmt9` has no such item. The Set's completion demonstration therefore pointed at nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten: each child pins its own matrix in a regression test, and `rlhmt9` V-05's final bare-suite run is the cross-child evidence. |
| PR-003 | MEDIUM | UNDER-SCOPE | G coverage / ownership | Completion criteria 1, 2, 3, 5, 6 carried no `Owner:` (only 4 and 7 did) | Criteria with no named owner are orchestrator-only obligations that the runner's retirement would skip. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each criterion now names its owning child plan and V-items. V-04 now cites owner evidence instead of re-measuring. |
| PR-004 | LOW | IN-SCOPE | G sequencing | E-03 "Depends on: E-02" vs child table `sjsb04` depends on `executed:i6mby8` only; E-04 listed only E-03 | The checklist dependencies did not match the child table. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now depends on E-01, and E-04 on E-01, E-02 and E-03, matching the table. |
| PR-005 | LOW | UNDER-SCOPE | G execution contract | Approval and execution gate | The gate lacked the honesty rule, the scope-fence declaration, the `aw commit`/never-push rule, and the conditional runner-vs-executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | An EXECUTION CONTRACT paragraph was added, and the finalize instruction was made conditional on runner vs hand execution. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the Set-level cross-child matrix be restored as a new child, or reframed as suite-plus-per-child evidence? | Reframed: each child's regression test plus `rlhmt9` V-05's final bare suite | Add an Order 05 "measure everything" child (duplicates four children's tests with no new behavior pinned) | `rlhmt9` V-05 "PASTE the BARE `python3 -m pytest` output"; per-child test files named in each child's E-items | yes |
| D-2 | Should the S408 repair loop spend attempt 2 by assigning `_nv_backend_args` to `sjsb04` or `rlhmt9`? | No; escalate to the maintainer as blocking OQ-03 | Assign to `sjsb04` (its "single-expression" risk profile excludes write-target changes); assign to `rlhmt9` (its scope fence forbids re-touching bypass sites) | `sjsb04` E-01/E-02 scope; `rlhmt9` scope fence "re-touch the six bypass sites (Order 03)" | yes |

## Round 2

Coverage-correction turn 1 of 2 (2026-10-07), driven by two `aw ipd coverage axozpe` `coverage-fail` quotes, both naming the PR-001 gap. Remedy applied per the coverage gate ("ADD A CHILD"): authored Order 05 `pua92o` (`.aw/records/plans/pending/20261007-dirsilent-05-pua92o-route-the-noun-verb-backend-adapter-through-resolve-verb-rep.ipd.md`, `to-review`, `- From-Backlog: rgl2d4`, `- Blocks-Release: next`, `- Item-Dependencies: executed:sjsb04`; `aw ipd lint --phase review-finalize` conforming). Added its row to the child table (rows: 4 -> 5), plus E-05/V-05 and the Scope-Paths entry. Assigned criteria 1 and 2 and the Deferred census row to `pua92o`. Resolved OQ-03 as option (a) and made it non-blocking. The checklist was not deleted (E-01..E-04 retained, E-05 added).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A correctness / coverage | `cli._nv_backend_args`; plan OQ-03 now `Status: resolved` | Seventh bypass site had no owning child. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owned by new child `pua92o`; OQ-03 resolved 2026-10-07. |
| PR-002 | MEDIUM | IN-SCOPE | G reachability | round 1 | unchanged | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | round 1 |
| PR-003 | MEDIUM | UNDER-SCOPE | G ownership | round 1 | unchanged | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | round 1 |
| PR-004 | LOW | IN-SCOPE | G sequencing | round 1 | unchanged | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | round 1 |
| PR-005 | LOW | UNDER-SCOPE | G execution contract | round 1 | unchanged | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | round 1 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Who owns `cli._nv_backend_args`? | New child Order 05 `pua92o`, climb only, no refusal | widen `sjsb04` (breaks its single-expression risk profile); decline and file backlog (leaves a known false-clean answer in a release-gated Set) | AGENTS.md coverage gate "WHEN IT FIRES, ADD A CHILD"; `rlhmt9` F-02 (index helpers single-class write); `lmyeas` OQ-01 | yes |
