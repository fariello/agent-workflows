- Id: ho7qjb
- Status: open
- Set: scoperewrite
- Priority: low
- Work-Kind: chore
- Summary: Decide whether to teach the status-agnostic Scope-Paths glob spelling as author guidance, which prevents stale record scope targets at the source with no code

## Workflow history
- 2026-10-02 created (aw backlog): Decide whether to teach the status-agnostic Scope-Paths glob spelling as author guidance, which prevents stale record scope targets at the source with no code

RAISED while authoring plan `5h3qyy` (Set `scoperewrite`, graduating backlog `es7wdp`) as that plan's F-03, and originally noted as F-10 of executed plan `guti33`. Filed as the durable carrier of `5h3qyy`'s deferred row. This is the ZERO-CODE alternative to the whole `scoperewrite` line of work: if plan authors spelled a record scope entry status-agnostically, the stale-target finding could not arise in the first place.

IT ALREADY WORKS TODAY, DRIVEN. For `.aw/records/backlog/**/<name>.backlog.md`: `ipd_schema._scope_path_entry_error` returns `None` (accepted); `parse_scope_paths` returns it intact and non-grandfathered; `ipd_lifecycle._scope_match` returns `True` against the same file under `open/`, `graduated/` AND `done/`, while returning `False` for a DIFFERENT file in the same directory, so the fence stays tight; and `check_engine.stale_record_scope_paths` returns `[]` for a plan declaring it, because that predicate skips any entry containing `*`, `?` or `[`. So no code change is needed to USE the spelling; the only question is whether to teach it.

THE TRADE-OFF THAT MAKES IT A DECISION. Driven: `ipd_lifecycle.scope_entry_is_literal_file` returns `False` for a glob entry, so such an entry is NOT eligible for rcptwiden `63425h`'s additive-widening accept at finalize. The reasoning is in that function's own docstring: a glob or directory entry can neuter a fence, so the widening path refuses it by design. Choosing the glob spelling therefore trades immunity-from-status-churn against widening-eligibility, and it slightly loosens the declared fence (any file matching the pattern in any status directory). That is a genuine contract trade a maintainer should rule on, not an obvious win.

WHY IT IS GUIDANCE AND NOT A CODE CHANGE. Adopting it means changing what every plan author writes, which is why executed plan `guti33` recorded the option (its F-10) but "does NOT mandate it (that would be a convention change for every plan author, well beyond a severity re-tier)" and plan `5h3qyy` likewise declines to mandate it unilaterally. If adopted, the natural homes are the plans README's Scope-Paths guidance and the IPD spec's scope section, plus possibly a `check` advisory nudging a literal records entry toward the glob form.

THE DECISION IS NOT URGENT AND NOT EXCLUSIVE. It composes with `5h3qyy` rather than competing: that plan's opt-in rewriter fixes entries authors already wrote literally, while this guidance would reduce how many get written that way. Either, both, or neither is a coherent posture.
