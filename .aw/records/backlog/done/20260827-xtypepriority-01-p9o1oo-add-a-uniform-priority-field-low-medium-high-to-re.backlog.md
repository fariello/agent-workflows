- Id: p9o1oo
- Status: done
- Set: xtypepriority
- Priority: medium
- Work-Kind: feature
- Summary: Add a uniform Priority field (low|medium|high) to research/plans/specs (backlog already has it); attention already reads Priority - extend the field + setters + checks + board rendering across types

## Workflow history
- 2026-08-27 done (aw set): Graduated into plan Set 'xprio' (orchestrator u5vyye; children 1b45el plans, rp859c specs, 6vgd0k research). Fresh setid xprio (NOT xtypepriority) per graduation policy (spec 4w7d6s); link in prose + orchestrator From-Backlog: p9o1oo note; machine-readable Graduated-To/From-Backlog owed once sjsoqq builds them.
- 2026-08-27 created (aw backlog): Add a uniform Priority field (low|medium|high) to research/plans/specs (backlog already has it); attention already reads Priority - extend the field + setters + checks + board rendering across types

Problem: only backlog carries `- Priority:` today (vocab `high|medium|low`, backlog.py:53); research, plans/IPDs, and specs have none, so they cannot be prioritized on the attention board. Decision: adopt a UNIFORM 3-level scale `low | medium | high` across research/plans/specs, matching backlog exactly (zero migration for backlog; reliably distinguishable by humans+agents, unlike a 7-level scale which produces inconsistent assignment + a noisier board). The 'urgent/drop-everything' case is already covered orthogonally by `Blocks-Release`, so no 4th tier.

Scope: add a recognized-but-optional `Priority` field (reuse backlog's `PRIORITIES = {high,medium,low}` vocab + `_PRIORITY_RE`) to the research frontmatter contract, the IPD schema (`META_RECOGNIZED`, recognized-but-optional like Scope-Paths/Blocks-Release), and the spec contract; add/extend the setters (`aw research set-*`/`new`, `aw ipd set`/`scaffold`, `aw specs set`) to write/validate it; validate the enum in `aw check`. `attention.py` ALREADY reads + renders `Priority` (backlog path) - extend the per-type record builders to populate `Item.priority` for the new types so the board sorts/labels them. Default when absent: unset (do not force a value; treat as unprioritized), or `medium` - decide at spec/impl.

Origin: user - "research, plans, specs, more or less everything need a priority." Related: the uniform `Summary` field decision (ud28vy) - same 'uniform recognized-but-optional field across all types + attention renders it' pattern.
