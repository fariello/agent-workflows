- Id: 7u9kbm
- Status: open
- Set: verifygap
- Priority: medium
- Work-Kind: feature
- Summary: no way to run the independent verifier turn against an already-executed plan: build_verifier_prompt has exactly one caller per host, inside the execute path

## Workflow history
- 2026-09-06 created (aw backlog): no way to run the independent verifier turn against an already-executed plan: build_verifier_prompt has exactly one caller per host, inside the execute path

THE GAP. The independent skeptical verifier EXISTS and is real: `build_verifier_prompt`
(`oc_runipd.py:4725`, `agy_runipd.py:2290`) composes a turn titled "Independent Rigorous
Verification of Executed IPD" that runs in a FRESH session with no inherited context, reads the
execution outcome JSON, and writes its own verification outcome JSON.

It has exactly ONE caller per host (`oc_runipd.py:6230`, `agy_runipd.py:3409`), both inside the
execute path, both gated on `validate`. So verification is available only as a second turn
immediately following an execution turn, in the same run. There is no way to ask for it later.

WHAT THAT COSTS. Three concrete situations, all of which occurred in this repository:
  * A run executed with validation OFF (the current default on the opencode host, by the maintainer's
    measured 2026-08-31 ruling). If you later want an independent opinion on one of those items, the
    only route is re-executing the plan, which is both expensive and wrong: the work is already done
    and the plan is already `executed`.
  * An item that reached `substantially-complete` because finalize refused (e.g. `nna8yz` in run
    `run-20260905T211011Z-3780617`, \$21.80 of work, finalize refused for a missing begin receipt).
    An independent verifier turn is exactly what a human would want before deciding whether to trust
    and integrate that lane, and it cannot be requested.
  * A plan integrated by hand during recovery (six lanes on 2026-09-05). Those merges were validated
    by the full test suite but never by an independent verifier, and there is no way to add that
    signal after the fact.

WHAT DONE LOOKS LIKE. A read-only-ish verb, e.g. `aw <host> verify <id6>`, that runs the EXISTING
verifier prompt against an already-executed plan and writes a verification outcome. It must NOT be a
second implementation: reuse `build_verifier_prompt` and the existing outcome schema, or the two
verifiers will drift and neither can be trusted (the same argument `wlxkoz` makes about not building
a second completion checker).

FOUR THINGS TO DECIDE, none of which the repository can settle alone:
  1. What does it verify AGAINST? The in-run verifier reads the execution outcome JSON for that
     attempt. For a plan executed weeks ago on a different HEAD, "the work" is a historical diff;
     verifying it against TODAY's tree answers a different question. Probably needs an explicit base
     (the plan's recorded base_head) rather than an implicit one.
  2. What may it WRITE? A verdict that contradicts an `executed` plan cannot silently reopen it: an
     executed plan must not be edited in place (repository policy), so a negative verdict should
     produce a corrective-IPD recommendation or a durable finding, not a status change.
  3. Does it need a lane? The in-run verifier runs in the worktree. A standalone one has no lane, and
     running it against the primary checkout while other agents work there is the contention problem
     `p8ni63`/`5wdoze` exist for.
  4. Is it wanted at all, given the economics? The maintainer's measured finding is that on the strong
     executor the verifier added only nits for ~33% cost. An after-the-fact verb inherits that
     question: if verification is not worth running DURING a run on that model, it may not be worth
     running after either. It is most valuable exactly where the in-run verifier is also most valuable
     - on a weaker executor - which makes this item's value CONDITIONAL on `h7qsje` (wiring the
     per-profile default) landing first.

SEQUENCING RECOMMENDATION: do `h7qsje` first. If per-model verification is wired and a weaker model
runs with validation ON, the in-run verifier covers most of the need and this verb becomes a recovery
tool rather than the primary path. Building it first risks adding a surface nobody invokes, for the
same reason nobody currently passes `--validate`.
