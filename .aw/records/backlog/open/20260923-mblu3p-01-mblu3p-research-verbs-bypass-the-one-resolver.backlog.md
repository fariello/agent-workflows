- Id: mblu3p
- Status: open
- Blocks-Release: next
- Set: mblu3p
- Priority: medium
- Work-Kind: bug
- Summary: aw archive/rename/group for research bypass the ONE resolver, contradicting selectors.py's documented single-resolver claim

## Workflow history
- 2026-09-23 created (aw backlog): Found while executing IPD xo3244 (selector YAML dialect).

MEASURED AT HEAD 0823163b while executing IPD `xo3244`.

WHAT IS WRONG. `selectors.py`'s module docstring (`:4-9`) states that "every verb (`rename`, `group`, `set`/`ipd set`/`spec set`/`backlog set`, `show`, `find`, `archive`, and the per-area set-assign/mv paths) routes selector resolution through `resolve()` here, so the SAME selector resolves to the SAME file for every verb". For RESEARCH that is false. `research_archive.py`, `research_cmd.py` and `research_refs.py` import `selectors` ZERO times and each re-implements selector matching with its own private loop over `_all_docs()`, matching only `parsed.id6 == target or parsed.set_id == target` against the PARSED FILENAME (`research_archive.py:305-312`, `:107-112`; `research_cmd.py:473`, `:598`; `research_refs.py:175`, `:203`).

THREE CONSEQUENCES, each verified.

1. THE SAME SELECTOR RESOLVES DIFFERENTLY PER VERB, which is precisely what the single-resolver design exists to prevent. Measured after `xo3244` landed: `aw find research reference` returns 64 documents (MATCH_STATUS), while `aw archive research reference` reports `no research doc or set matches 'reference'` and `aw rename research reference` reports `error: no research file has id6 'reference'`.

2. THE FILENAME IS THE AUTHORITY RATHER THAN THE DECLARATION. These verbs read `parsed.id6` from `parse_name(p.name)`, so a research document whose filename slot disagrees with its declared `id:` is reached by its filename and not by its identity. That is the inverse of the ARTIFACTS-NOT-MENTIONS rule the resolver enforces, and it is the same class of defect IPD `76w6mq` fixed inside the resolver.

3. FOUR SELECTOR KINDS ARE SIMPLY UNAVAILABLE for these verbs: `path`, `status`, `stem` and `substring`. There is also no `resolve_for_mutation` ambiguity policy, so no `UNIQUE_KINDS` collision refusal and no `--force` semantics on a verb that MOVES files.

WHY IT IS FILED AS A BUG RATHER THAN A CHORE. The user-visible symptom is that a documented uniformity guarantee does not hold on a MUTATING verb: an operator who learns a selector from `aw find` and reuses it on `aw archive` gets a silent no-match rather than the documented behavior or an error explaining the difference.

HONEST SCOPE NOTE, so this is not over-claimed. This bypass is also what made `xo3244` SAFE: because `aw archive` never consults the resolver, teaching the resolver the YAML dialect did NOT widen any mutating verb. Verified before/after with the resolver change stashed: `aw archive research archive|reference|todo` is byte-identical (all three: no match), and `aw archive research awmetastore` previews the same 7 documents. `xo3244`'s OQ-01 recorded a maintainer decision accepting a widened mutating surface on the belief that `aw archive` routed through the resolver; that consequence did not in fact occur, and the reason is this defect. So FIXING this defect is what would finally deliver the widening OQ-01 already approved. Whoever takes it must treat that as a deliberate, separately-evidenced change and not a refactor side effect: routing these verbs through `resolve` would make `aw archive research archive` start relocating 32 documents where it moves none today.

WHERE. `agent_workflows/research_archive.py` (`run_archive`, `plan_transition`, `_all_docs`), `agent_workflows/research_cmd.py:473`/`:598`, `agent_workflows/research_refs.py:175`/`:203`, against the claim in `agent_workflows/selectors.py:4-9`.
