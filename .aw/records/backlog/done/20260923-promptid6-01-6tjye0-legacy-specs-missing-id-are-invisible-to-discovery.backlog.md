- Id: 6tjye0
- Status: done
- Set: promptid6
- Priority: low
- Work-Kind: chore
- Summary: The naming spec 20260730-2152-01 carries no '- Id:', so it is invisible to discover_specs and cannot be named by an id6 selector

## Workflow history
- 2026-09-26 done (aw set): Retired MOOT (maintainer 2026-09-25 spec 4sd62s, Blocks-Release next): 4sd62s 5.2 step 3 mints an id6 for every lifecycle record lacking one (19 of 38 specs at 2026-09-26, not 2) and routes every reader through artifact_meta, so converting two now would be churned again by the one-commit migration.
- 2026-09-23 created (aw backlog): The naming spec 20260730-2152-01 carries no '- Id:', so it is invisible to discover_specs and cannot be named by an id6 selector

FOUND AT REVIEW AND RE-CONFIRMED WHILE EXECUTING IPD ubac5n (promptid6), which had to AMEND that spec and could only cite it BY PATH.

WHAT IS WRONG: .aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md (and its sibling .aw/records/specs/20260817-2147-01-uniform-artifact-naming-grammar.spec.md, both amended by ubac5n) carry a legacy YYYYMMDD-HHMM-NN name and NO '- Id:' bullet. specs.discover_specs keys on the declared id6, so neither spec appears in its records at all. Consequences: no 'aw spec set <id6>' on them, no id6 citation from a plan's From-Spec:, and no appearance in an id6-keyed view. They ARE resolvable by stem ('aw find specs agents-artifact-organization').

RELATED BUT DISTINCT, already visible in 'aw check all': check.identity-absent-from-name fires on two OTHER specs (20260826-0718-01-aw-run-deterministic-run-and-verify, 20260824-2000-01-research-lifecycle-reliability). So this is a small population, not a sweep.

THE TOOL EXISTS: 'aw rename specs <legacy> --to-id6 --apply' mints the id6, injects the '- Id:' bullet (correct for a spec, which does carry front-matter bullets) and rewrites citations. Verified during ubac5n execution against a fixture: the spec path is byte-unchanged by that plan's prompts repair.

WHY ubac5n DID NOT DO IT: it only AMENDED those specs' bodies; renaming an artifact it merely cites would have enlarged its blast radius into the spec tree, and the spec is heavily cited by path across the repository.

CAUTION: both specs are '- Status: implemented' and are cited BY PATH in many places. A conversion must let the reference rewriter update those citations, and 'aw rename --to-id6' fails loud on a full-path citation naming a different directory, so run the preview first.
