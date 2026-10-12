# Review findings: plan 69pxm5

- Subject-Id: 69pxm5
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `ebe34e463`. The plan was committed and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. Not an orchestrator.

Verified:
- `artifact_refs.classify_citing_plans_for_rewrite(repo_root, candidate_files) -> (rewritable, must_skip)`
  exists, fails closed on a present receipt or a missing `- Id:`.
- `grep -c receipt` is 0 for `artifact_rename.py`, `plans_refs.py`, `research_refs.py` and `plans_archive.py`.
- The four planning sites exist as named: `artifact_rename.run_rename_generic`; `run_group_generic` (per
  target, `all_edits`/`all_warnings` de-duplicated); `plans_refs.apply_renames`; `research_refs._apply_renames`.
- Each site prints its warnings and carries them into `MutationResult.notes` on both preview and apply.
- `cli.map_mutation_result_to_command_result` surfaces notes as `Evidence(key="notes")` and `data["notes"]`.
- Both `RefEdit` shapes expose `.file`.
- The repository has no non-`.ipd.md` plan file other than the `README.md`/`STATUS.md` manifests.
- D162 is the highest decision, and spec 4.5 carries the quoted "rewriting citations by the stable id." sentence.

F-01 RE-REPRODUCED on a scratch repo through `cli.main`, with the in-flight plan's receipt present: `group
specs`, `rename plans` and `rename research` each rc 0, in-flight plan changed True.

E-02/E-03 DESIGN DEMONSTRATED by wrapping the three backends' `plan_reference_rewrites_with_warnings`
with a prototype of the filter that calls `classify_citing_plans_for_rewrite`. Result on all three backends,
apply and preview:
- the in-flight plan is unchanged;
- the sibling plan with no receipt is rewritten;
- the `tests/` file is rewritten (group specs);
- rc is 0 and a SKIPPED line is printed;
- no `would rewrite` line names the in-flight plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric E (evidence feasibility) | `cli.map_mutation_result_to_command_result` (`Evidence(key="notes", ...)`); measured compact `--agent` record `"evidence":["notes"]` | E-04(h) asked for the skip note "in its evidence/notes" under `--agent`. The compact record projects evidence to key names, so the note text is absent and a test written as specified would fail or be weakened. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (h) now asserts evidence names `notes` under `--agent` and the SKIPPED text in `data.notes` under `--json` (measured present there and under `--agent --verbose`). |
| PR-002 | MEDIUM | UNDER-SCOPE | Rubric D; backlog `23p80m` (stranding cost class) | measured: `aw rename plans p22222 --slug renamed --apply` with `p22222`'s receipt present -> rc 0, executing plan's file renamed | Renaming the IN-FLIGHT plan itself is a sibling hazard that an edit filter cannot reach (it is a file move). The plan neither named it nor handed it off, and its close of `23p80m` would lose the observation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-07 with the reproduction; E-04(i) pins today's behavior; a deferred row plus new E-08/V-08 file it as its own backlog item before close. |
| PR-003 | LOW | IN-SCOPE | Rubric G | `artifact_refs.RefEdit.file` (absolute in practice), `research_refs.RefEdit.file` | E-02 said only "resolved relative to `repo_root`". Edit files arrive absolute, and a naive relative join or string compare would miss the match. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now specifies resolving and comparing by `Path.resolve()`, and never dropping a file outside `repo_root`. |
| PR-004 | LOW | UNDER-SCOPE | Rubric G (scope declaration) | E-08 writes a minted-id6 backlog file | The new file cannot be named in `- Scope-Paths:` ahead of time. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope check and deferred row say it is justified at finalize with `--scope-reason`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Accept the author's OQ-01 (skip and report, mirroring D159)? | Accept. | Refuse the rename; rewrite and re-freeze (both REJECTED for the reasons OQ-01 cites). | `DECISIONS.md` D159; prototype run. | yes |
| D-2 | Fix the in-flight self-rename here, or hand it off? | Hand off (F-07, E-08), and pin current behavior. | Guard it in this plan (REJECTED: a different mechanism, a file move, and whether it strands a lane is unmeasured, so it needs its own design and review). | measured self-rename; `ipd_lifecycle.receipt_path_for` keys on id6. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
