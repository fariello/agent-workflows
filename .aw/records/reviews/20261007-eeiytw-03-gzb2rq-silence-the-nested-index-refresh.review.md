# Review findings: plan gzb2rq

- Subject-Id: gzb2rq
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-301 (HIGH, fixed), PR-302 (MEDIUM, fixed), PR-303 (MEDIUM, fixed), PR-304 (HIGH, fixed), PR-305 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `208a3a35b`. The plan was committed and byte-identical to the lane input. Before
review, `aw ipd lint --phase author` was `clean`; after revision, `--phase review-finalize` was `clean`. The plan is a child.
Orders 01 (`x7unul`) and 02 (`vfqjc0`) were hardened earlier in this sweep, and their revisions bear on this plan.

Verified: `plans_index.run_index` gates its drift loop and outcome lines on `quiet` (on the regenerate path only).
`research_index.run_index` gates both its drift print and its outcome lines on `quiet` and returns 1 without writing on
drift. `status_set._auto_index_types` passes `quiet=True` and appends Changes based on existence. The only tests asserting
the `wrote ... INDEX.json, INDEX.md` text are direct `run_index` tests (`test_plans_index`, `test_research_index`), which
this plan does not affect. A throwaway-repo measurement found the nested line is the whole stdout of `group plans --apply`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | UNDER-SCOPE | D/F silent failure | `research_index.run_index` regenerate branch (`if drift: if not quiet: print(...); return 1`); `x7unul` F-10 | `quiet=True` also silences the research drift lines. Those lines are the only human signal that the manifest was NOT refreshed. The plan did not state this second human-output change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires one stderr warning in human mode when the nested rc is non-zero. Machine mode relies on Order 01's rc-keyed diagnostics. V-02(f) added. |
| PR-302 | MEDIUM | IN-SCOPE | A truthful reporting | `status_set._auto_index_types` (`if idx_json.exists(): changes.append(...)`) | Copying the precedent would report "auto-refreshed" when research refused on drift and wrote nothing, which contradicts Order 01's not-regenerated note in the same record. The carrying layer was also left undecided. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Change is now keyed on the nested rc. The layer is fixed: a new optional `MutationResult` field plus one mapper line. `cli.py` is declared for that line. V-03(e) and F-10 added. |
| PR-303 | MEDIUM | IN-SCOPE | Evidence accuracy | A fresh repo leaves `?? .aw/records/plans/INDEX.json` (not ignored); this repo has `.aw/.gitignore:45` | The plan called the manifests "gitignored", but that is only true for this repository. In a target repo, an accidental `touched_paths` addition would really stage them, while in this repo git hides the mistake. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Wording corrected. V-03(f) now requires the commit-path check in a repo without the managed ignore. F-09 added. |
| PR-304 | HIGH | UNDER-SCOPE | D cross-plan tests | `x7unul` E-05(c) and `vfqjc0` E-06(f) byte-equality expectations, which include the nested line | E-01 and E-02 would turn both Orders' byte-equality tests red. The plan only tightened Order 02's machine assertions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04(f) deletes the named nested-line fragment from both expectations. `tests/test_mutation_result_facts.py` declared. V-04(h) added. |
| PR-305 | LOW | IN-SCOPE | G gate accuracy | `87m438` in `executed/` | The gate names a stale concurrent-edit plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to the Set's own Orders. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where should a refused research regeneration be reported for humans? | One stderr warning line, suppressed in machine mode. | (a) Keep the drift lines on stdout: they are nested output on the outer stdout, the same defect. (b) Say nothing: a silent failure. | `docs/cli-output-contract.md` Sections 11.2 and 11.4; `research_index.run_index` | yes |
| D-2 | What key decides whether a manifest Change is reported? | The nested call's rc (0 means regenerated or up to date). | File existence, as `status_set` does: it misreports a refused refresh. | `research_index.run_index` return 1 on drift | yes |
| D-3 | Which layer carries the manifest entry? | A new optional `MutationResult` field, mapped in Order 02's mapper. | Append at the dispatch site: that layer does not know the nested rc or the resolved manifest directory. | `plans_refs.MutationResult`; the backends hold the rc | yes |
