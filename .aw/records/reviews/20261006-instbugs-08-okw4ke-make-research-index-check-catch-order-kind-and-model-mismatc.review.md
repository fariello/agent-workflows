# Review findings: plan okw4ke

- Subject-Id: okw4ke
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `5d7909cc6` in an isolated review-sweep lane. Child plan (`- Kind: child`). Plan committed and
byte-identical to the lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent` clean before semantic
review; `--phase review-finalize` clean after revisions.

Verified:
- `research_index._doc_entry` block "# name-vs-frontmatter consistency" compares only `fm.get("id") != parsed.id6` and
  `fm.get("set") != parsed.set_id` (F-01 holds).
- Scratch `private-target` install with `AW_NO_REEXEC=1` and temp `HOME`, two `aw research new --apply` files (one with
  `--model gpt56`), `aw research index`, then probes: `order: 05`, `kind: findings`, `kind: research`, `model: gpt56` on a
  no-facet name, `model:` empty and `model: reconciliation` on a `.gpt56.` name all exited 0 with no mismatch line;
  `order: 1` exited 1 with `frontmatter-invalid: order: order must be a two-digit string NN`; a changed id printed
  `name-frontmatter-mismatch: id zzzzz9 != name fuclk7`.
- The proposed rules (string order, normalized kind, name-side-only model) applied by hand to this repo's 128
  front-matter-valid research records: 0 hits.
- This repo's `aw research index --check` exits 1 today (35 adopted-without-consumer, 122 dangling-citation,
  19 stale-state-to-promote, 1 frontmatter-invalid, 2 stale-index-missing).
- `aw check research` and `aw check all` did not report a changed id (exit 0): `check_engine.check_content` calls
  `research_index.check_drift` only under `include_retired`.
- Commit `e21ba4378` (`ax8eg1`) exists; research `l6cbbb` D10 matches the Concern.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A Correctness / E Testing | `agent_workflows/research_contract.py:493-498` `validate_frontmatter` "order must be a two-digit string NN"; `agent_workflows/research_index.py:108-112` early return | Integer order compare and the `order: 1` clean test are unreachable: `order: 1` is already `frontmatter-invalid` and never reaches the comparison, so E-04's clean assertion would fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Plain string compare; `order: 1` clean case removed from Scope, E-02, E-04. |
| PR-002 | HIGH | IN-SCOPE | D Domain invariants | spec `20260730-2152-01` Section 4.4 "`<model>` is present ONLY when authorship disambiguation matters, and always ALSO recorded in frontmatter" | "present on one side only is a mismatch" would flag every legal front-matter-only model, contradicting the spec. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Model compared only when the filename carries the facet; front-matter-only model added as a clean test case. |
| PR-003 | MEDIUM | IN-SCOPE | A Correctness | `research_contract.parse_name` returns `kind_res.value` and `model_res.value` (normalized); `KIND_NORMALIZATIONS` `"research": "research-report"` | Raw compare of front matter kind/model against normalized name values would false-flag legal aliases (e.g. `kind: research`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 normalizes front matter via `normalize_kind`/`normalize_model`; alias case added as clean control. |
| PR-004 | MEDIUM | IN-SCOPE | G Executability | this repo `aw research index --check` exit 1 with unrelated drift classes | E-03/V-03 demanded this repo "check clean", unsatisfiable for reasons outside scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bar narrowed to zero `name-frontmatter-mismatch` lines, re-derived at execution; corrections justified with `--scope-reason`. |
| PR-005 | LOW | IN-SCOPE | E Testing | E-01 "add `model: gpt56` to a filename without a model facet" | Probe set did not exercise the model case that the corrected rule flags (name facet vs differing/empty front matter) and gave no reproducible install recipe. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now four concrete probes on a `private-target` install; V-01/V-02 updated to four probes plus clean controls and diff. |
| PR-006 | HIGH | UNDER-SCOPE | Project rule (Every live bug gates the next release) | `AGENTS.md` live-bug rule; `- Work-Kind: bug` without `Blocks-Release`; `i99ykd` review PR-002 | Live bug plan did not gate release `next` (`f33nrj`, planned). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Blocks-Release: next`. |
| PR-007 | MEDIUM | UNDER-SCOPE | G Execution contract | gate "move the plan to `executed/` with `aw ipd set executed okw4ke`" | Gate lacked resolved-OQ statement, honesty rule, scope fence as declaration, temp HOME, and conditional finalize ownership; used `aw ipd set executed` instead of `aw ipd finalize`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to the Set's standard contract. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a front-matter model with no name facet be a mismatch? | No | Flag it (plan as authored) | spec `20260730-2152-01` Section 4.4; `research_cmd` writes `model:` regardless of name facet | yes |
| D-2 | Should an empty front matter model on a name with a facet be a mismatch? | Yes | Treat empty as "unknown, skip" | Section 4.4 "always ALSO recorded in frontmatter"; filename is canonical (OQ-01) | yes |
| D-3 | Extend the fix to `aw check research`/`all` not running `check_drift` without `include_retired`? | No; recorded in Scope check and reported to maintainer | Add to this plan | Plan goal names `aw research index --check`; different surface and gating semantics in `check_engine.check_content` | yes |
