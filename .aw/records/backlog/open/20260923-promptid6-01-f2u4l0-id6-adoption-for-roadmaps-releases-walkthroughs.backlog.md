- Id: f2u4l0
- Status: open
- Set: promptid6
- Priority: low
- Work-Kind: chore
- Summary: Roadmaps, releases and walkthroughs still carry no id6, so the uniform artifact grammar has three remaining holdouts

## Workflow history
- 2026-09-23 created (aw backlog): Roadmaps, releases and walkthroughs still carry no id6, so the uniform artifact grammar has three remaining holdouts

DEFERRED BY IPD ubac5n (promptid6). AGENTS.md states ONE uniform artifact-naming grammar, YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md. Four types had not adopted it; ubac5n moved PROMPTS (following ha55fi, which moved specs), leaving three.

WHAT IS LEFT, per agent_workflows/artifact_naming.py's id6-less enumeration (now naming exactly these three): roadmaps, releases, walkthroughs.

CONSEQUENCE, the same one that motivated prompts: every aw verb resolves an artifact BY id6, so an id6-less artifact is invisible to aw find and cannot be named in a From-*/Blocks-Release/consumed-by field. Measured 2026-09-23: 'aw check all' reports check.name-nonconformant on 2 walkthroughs and 1 roadmap today.

EACH IS ITS OWN MIGRATION, deliberately: doing all three at once would make one review cover three vocabularies, which is the same reason ubac5n did prompts alone.

THE SHAPE IS NOW ESTABLISHED TWICE (ha55fi for specs, ubac5n for prompts) and is reusable: (1) mint via artifact_core.mint_id6 and build via artifact_naming.build_clustered_name in the type's producer; (2) register cutovers.<type>_id6 in config.KNOWN_FEATURE_CUTOVERS and add a _<type>_requires_id6 twin of check_engine._prompt_requires_id6 (config-first with a non-None module fallback); (3) correct every doc surface asserting the id6-less choice; (4) let 'aw rename <type> --to-id6' convert on demand.

ONE BLOCKER TO RESOLVE FIRST for walkthroughs and roadmaps: see backlog a88210. The shared '- Id:' injector anchors the bullet under the H1 when a file has no Status/Date bullet, and many walkthroughs/roadmaps have none, so --to-id6 would write metadata into their body. Fix that before converting either type.

ALSO NOTE walkthroughs have an extra rule: DECISIONS D140 says a walkthrough's filename identity slot must be its OWN id6 and must NOT reuse the id6 of the plan it documents (the link is the Target-Id: field), enforced by check.id6-identity-slot.
