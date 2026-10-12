# Review findings: plan sn2svz

- Subject-Id: sn2svz
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `cec043bab`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize --agent` both reported `clean`. `- Kind: child`.

Re-measured in temp fixture repos, with no tracked file changed (recorded as F-09 in the plan). F-01, F-02 and F-03 reproduce exactly. A hand-built `index` result/findings `CommandResult` of the planned shapes validates `[]`. `index` is a `read`/`result` declaration, so removing its exemption puts it in `UNIVERSE`, and live `index plans --check --agent` keeps exit parity (1/1). No test asserts `"research index"` as a `cmd`. All four carrier backlog items exist.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (vacuous regression probe) | Review run: `rename plans aaaaaa --slug renamed --agent` (preview) leaves the plans dir `['pending']` (no index written); with `--apply` it becomes `['INDEX.json','INDEX.md','pending']`, still one stdout line; `plans_refs.apply_renames` returns its preview `MutationResult` before the `_idx.run_index(...)` call | E-08(3)'s internal-caller silence probe used the PREVIEW form, which never reaches `run_index`, so it would pass even if the new branch printed a second record. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The probe now uses `--apply` and also asserts that both index files exist, which proves `run_index` ran. V-08 updated to match. |
| PR-002 | MEDIUM | IN-SCOPE | A (interface ambiguity) | E-02 signature lacked any pre-write existence parameter while requiring `create` vs `update`; all three `run_index` write paths overwrite before any emit | "The caller passes which existed, or the helper is told before the write" left the `Change.kind` source undefined. After the write, existence cannot be recovered. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `json_existed`/`md_existed` to the signature, read by each caller BEFORE its write. E-03 updated to match. |
| PR-003 | MEDIUM | IN-SCOPE | G (scope-fence wording) | Scope check: "update the assertion in that test only if it is in Scope-Paths, otherwise stop and record it" | This is the out-of-scope-edit STOP directive the 2026-09-01 ruling forbids. The fence is a declaration, and an out-of-scope edit is made and justified at finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to make-and-justify with `--scope-reason`, citing the review measurement that no such test exists. |
| PR-004 | LOW | IN-SCOPE | E (fixture feasibility) | Review run: `_write(..., created="2026-07-01")` -> `name-invalid` refusal; `RESEARCH_ROOT = ".agents/docs/research"`; `status="bogus-status"` -> `frontmatter-invalid` | E-01 did not pin the research fixture details, and a natural dashed date silently turns every research case into a refusal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 pins the `YYYYMMDD` date, the `.agents/docs/research` location for `changes` paths, and the `bogus-status` recipe for the refusal case. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How does the emitter learn create vs update? | Explicit `json_existed`/`md_existed` arguments read before the write. | Infer from `*_changed` (cannot distinguish create from update); drop the distinction (loses the Section 11.3 change kind). | `plans_index.run_index`, `prompts_index.run_index`, `research_index.run_index` write before any emit. | yes |
