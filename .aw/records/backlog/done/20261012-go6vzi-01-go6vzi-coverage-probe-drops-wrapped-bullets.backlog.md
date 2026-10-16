- Id: go6vzi
- Status: done
- Graduated-To: go6vzi
- Blocks-Release: next
- Set: go6vzi
- Priority: medium
- Work-Kind: bug
- Summary: Orchestrator coverage probe drops wrapped bullet continuation lines, so an OWNER on the second line is invisible and the run falsely refuses

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD u1l9rx executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-go6vzi-01-u1l9rx-keep-wrapped-prose-bullet-and-paragraph-continuations-in-una.ipd.md); evidence .aw/records/plans/executed/20261014-go6vzi-01-u1l9rx-keep-wrapped-prose-bullet-and-paragraph-continuations-in-una.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: u1l9rx
- 2026-10-12 created (aw backlog): found unblocking aw oc run on m0kl28

## What happened (measured 2026-10-12)

`aw oc run ... m0kl28 ...` refused at RUN-STRUCTURE-PREFLIGHT with three IPD-S408 `coverage-fail` findings on orchestrator `m0kl28`, quoting three `## Completion criteria` bullets. Each bullet DID name its owner (`OWNER: nxh5s4 (executed)`, `OWNER: nxh5s4 and rozdkp`), but on the WRAPPED, indented second line of the bullet.

## Root cause

`ipd_lint.unattached_section_prose` (the extractor behind `runner_shared.probe_cache_payload` / `orchestrator_probe_excerpt`) drops every indented line ("any indented line (leading space or tab)") so it stays disjoint from E-item continuation lines. For a hard-wrapped prose BULLET, that removes the bullet's continuation, so the model sees only the truncated first line (`- A capability on ... set True`) with no owner, and the prompt's "any doubt resolves to CONTAINS EXECUTIONS" rule correctly fails it. Five consecutive `coverage fail` history lines on 2026-10-11 show the loop this produces: each re-check sees the same truncated text.

Confirmed: joining each bullet onto one line (commit 592bfbf0b) made `aw ipd coverage m0kl28` pass with no other change.

## Fix

In `unattached_section_prose`, keep an indented line when it continues an unattached prose bullet or paragraph (i.e. the previous kept line in the same section is a non-leaf line), and still drop indented lines that follow a checklist leaf or subfield. Join the continuation onto its bullet so the excerpt carries whole bullets. Behavioral test: an orchestrator whose completion-criteria bullet wraps `OWNER: <child id6>` onto a continuation line yields an excerpt containing that owner text; an E-leaf's indented continuation is still excluded. Note: this changes the coverage fingerprint of any orchestrator with wrapped prose bullets, so their records go stale once and are re-probed.

## Workaround

Put the owner on the bullet's first line (or unwrap the bullet).
