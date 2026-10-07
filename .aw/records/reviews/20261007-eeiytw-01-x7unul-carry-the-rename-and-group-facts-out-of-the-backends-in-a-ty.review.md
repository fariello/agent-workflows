# Review findings: plan x7unul

- Subject-Id: x7unul
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `5cbee7c94`. The plan was committed and byte-identical to the lane
input, so there was no pre-review snapshot. `aw ipd lint --phase author --agent` returned `clean` before review, and
`--phase review-finalize` returned `clean` after revision. The plan is not an orchestrator (`- Kind: child`), so
S407/S408 do not apply.

Verified against code: `plans_refs.MutationResult` is `(rc, touched_paths=())`; `apply_renames` returns `()` on preview;
`run_rename_generic`/`run_group_generic` carry the dead plans/research index blocks the plan says to leave alone;
`run_group_generic` prints `set metadata Set:` separately (F-04); `rg -l MutationResult tests/` is empty; the only
readers are `cli._run_noun_verb` and the `research_cmd in ("set-assign", "mv")` branch; no caller tuple-unpacks a
backend result; `result_types.Change`/`Diagnostic` have the fields the Order 02 mapper expects.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric A/G (correct premise, feasibility) | `agent_workflows/research_index.py` `run_index` regenerate branch (`if drift: ... print(f"{d.location}: {d.rule}: {d.detail}") ... return 1`); `agent_workflows/research_refs.py` `_apply_renames` (`_ridx.run_index(...)` inside `except Exception: pass`) | E-04 said `research_refs` "PRINTS A FRONTMATTER VALIDATION BLOCK" and told the executor to "carry" it into `diagnostics`, as though the facts were already in hand. They are not. The lines come from the nested index regeneration, which scans every research doc, refuses to write the manifest, and returns 1, and `research_refs` discards that rc. So the specified capture was impossible as written, and an executor would have had to guess one of three mechanisms (capture stdout, edit `research_index` (out of scope), or re-scan). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-10 with a demonstration from a throwaway repo (quiet rc=1, `_scan_docs` returns exactly the printed drift, 85-340ms re-scan). E-04 now names the mechanism: capture the nested rc, re-scan only on the drift path, record `severity="warning"` diagnostics plus a not-regenerated note, leave `research_index.py` and the Namespace untouched, and keep rc 0. Added V-04(b)/(b2) and E-05(a2), and corrected F-03 and Proposed change 4. |
| PR-002 | MEDIUM | UNDER-SCOPE | Rubric E/G (verification strength) | `rg -n "return MutationResult\(2\)" agent_workflows/plans_refs.py` lists 9 sites (3 in `run_set_assign`, 6 in `run_mv`), against E-02/V-02's "four refusal paths" | E-02 and V-02 only required four refusal paths, so an executor could leave five `plans_refs` exit-2 sites without a diagnostic and still pass. V-03 had no refusal check at all, though `artifact_rename` has 13 sites. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires every exit-2 site (count re-derived at execution). V-02(c) checks off each site by its message and adds the `--allow-invalid-order` note case. Added V-03(e). |
| PR-003 | MEDIUM | UNDER-SCOPE | Rubric G (completeness of facts) | `plans_refs.apply_renames` / `artifact_rename` / `research_refs._apply_renames` `for w in warnings: print(w)`; `artifact_rename` `_id6_write_message`, `reuses existing`, `--- WARNING: full-path citation`; `research_refs` `warning: destination ... not a conformant research document`, `warning: could not update frontmatter` | `notes` listed only the setid warning and the override note. Several other printed lines had no field, so Order 02's prose suppression would leave them on no surface at all, and nothing checked for that. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now lists these and adds a COMPLETENESS RULE: every printed line except nested index output maps to exactly one fact. V-02(c2) and V-03(e) check it. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric A (data integrity of reported facts) | `plans_refs.apply_renames` (`ref_edits = _refs.filter_test_edits_interactive(...)` before applying); same in `artifact_rename` and `research_refs` | The plan did not say whether `ref_edits` meant the planned edits or the applied ones. The interactive filter can drop `tests/` edits, so the pre-filter list would report rewrites that never happened. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now says applied (post-filter) on `--apply` and planned on preview, and binds E-03/E-04 to the same rule. V-02(c2) checks it. |
| PR-005 | LOW | IN-SCOPE | Rubric D/E (test lifecycle across the Set) | E-05(c); Order 03 `gzb2rq` E-01/E-02 deliberately remove the nested index line | The byte-equality test pins the nested index line that Order 03 deliberately removes, and it did not say to record the expectation from HEAD. That invited recording post-change output, and it would make Order 03's edit look like a test rewrite. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05(c) now requires the expectation be recorded from HEAD and the nested line be kept as a separately named fragment, so Order 03 is one visible deletion. Added a Deferred row (Carrier `gzb2rq`): Order 03's research `quiet=True` also silences the drift lines. |
| PR-006 | LOW | IN-SCOPE | Evidence drift | `rg -n "MutationResult\(" agent_workflows/` gives 34 construction sites, against the plan's "19" in E-01 and F-07 | The count was an undercount. It did not change the design (widening stays the right choice), but it is a stale citation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 and F-07 now carry the re-measured figure and a re-derive instruction. F-07 also records the no-tuple-unpacking check. |
| PR-007 | LOW | IN-SCOPE | Rubric G (execution contract accuracy) | `.aw/records/plans/executed/20260929-awrenamesel-02-87m438-...ipd.md` | The gate warned of concurrent edits from "pending plan `87m438`", but that plan is executed. The real overlap is the Set's own Order 03. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate stop condition reworded. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `research_refs` obtain the nested index's drift findings without changing output or editing `research_index.py`? | Capture the nested `run_index` rc. On a non-zero rc, re-run `research_index._scan_docs` and map each drift to a `warning` diagnostic, plus a not-regenerated note. | (a) Redirect and parse the nested call's stdout: brittle, and it would couple facts to prose that Order 03 silences. (b) Add a return-facts API to `research_index`: out of scope, and it changes a shared verb for one caller. (c) Drop the lines from the facts: the machine surface would lose information the human sees. | Demonstrated in a throwaway repo (F-10): quiet rc=1, `_scan_docs(...)[1]` equals the printed drift; cost 85-340ms only on the drift path | yes |
| D-2 | Does `ref_edits` report planned or applied edits? | Applied (post-`filter_test_edits_interactive`) on apply, planned on preview. | Pre-filter list: it misreports declined `tests/` rewrites. | `plans_refs.apply_renames` filter-then-apply sequence | yes |
| D-3 | What are the semantics of the nested plans index drift lines? | Not captured. They are index output with no mutation consequence (`plans_index.run_index` writes regardless and returns 0), and Order 03 silences the call. | Capture them like research: no consequence to report, and it adds a 2.5s re-scan on this repo. | `plans_index.run_index` ("metadata drift ... is reported but does NOT block the write"); measured `scan_plans` 2486ms over 1325 plans | yes |
