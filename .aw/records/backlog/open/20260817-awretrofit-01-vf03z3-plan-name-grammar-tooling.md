- Id: vf03z3
- Status: open
- Set: awretrofit
- Priority: medium
- Kind: bug
- Summary: Plan-name tooling: scaffold/mv/plan-names/AGENTS.md disagree on the Set-clustering filename grammar

## Workflow history
- 2026-08-17 created (aw backlog): Plan-name tooling: scaffold/mv/plan-names/AGENTS.md disagree on the Set-clustering filename grammar
- 2026-08-17 promoted (opencode Opus 4.8): all four gaps are folded into spec 20260817-2147-01 (uniform artifact-naming grammar) as goals G2/G4/G5/G7. Kept OPEN and linked; close as "promoted to spec" once that spec is approved, so the fixes ship as part of the naming-grammar work rather than as separate one-offs. Also add: `aw backlog set` cannot resolve a blocked/ item by id, and Gate-Kind rejects 'spec' (release-review finding S5-DC02).

Discovered during release-review run 20260817-153418 while /plan-review-ing the awretrofit Set. Four related defects in the plan-naming tooling/docs:
1. aw ipd scaffold does not derive/enforce the canonical Set-clustering filename (YYYYMMDD-<set-id>-NN-<id6>-<slug>.md); it wrote whatever --path was passed, producing a hybrid YYYYMMDD-HHMM-NN-<setid>-<slug> that dropped the id6 and kept HHMM.
2. aw plans mv rewrites the in-file '- Order:' metadata to 0 when --order is not passed (should preserve/parse the existing order from the file or the new NN). Had to restore Order manually after renaming the awretrofit Set.
3. aw plan-names does NOT flag a Set-clustered plan that violates the YYYYMMDD-<set-id>-NN-<id6>-<slug> grammar (it accepted the hybrid names silently).
4. AGENTS.md documents TWO conflicting grammars: line 26 (Set-clustering, with id6, no time) vs line 51 (lifecycle, YYYYMMDD-HHMM-NN-<slug>, no set-id/id6). Reconcile: state that a Set-member (Set: present) uses the clustering grammar and a standalone plan uses the lifecycle grammar, or unify.
Fix scope: make aw ipd scaffold emit the canonical name when --set is given; make aw plans mv preserve Order; make aw plan-names validate the clustering grammar for Set members; reconcile the AGENTS.md/managed-block wording.
